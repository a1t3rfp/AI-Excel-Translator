from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import re
import json
import os
import config
from config import TARGET_LANG

MODEL = "facebook/nllb-200-distilled-600M"

print("Loading AI model...")

tokenizer = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL)

print("Model loaded.")

tokenizer.model_max_length = 512
tokenizer.src_lang = "eng_Latn"

FIXES = {
    "IALA Dəniz Dəmir Dəmiri Sistemi": "IALA Maritime Buoyage System",
    "IALA Dəniz Buoyage Sistemi": "IALA Maritime Buoyage System",
    "Quick Flash": "Quick Flash",
    "Very Quick": "Very Quick",
}

class LocalTranslator:

    def __init__(self):

        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        model.to(self.device)

        print("Using:", self.device)
        self.cache = {}
        self.load_memory()

    def load_memory(self):

        if config.TARGET_LANG == "azj_Latn":
            self.memory_file = "translation_memory_az.json"
        else:
            self.memory_file = "translation_memory_tr.json"

        if os.path.exists(self.memory_file):
            with open(self.memory_file, "r", encoding="utf-8") as f:
                self.memory = json.load(f)
        else:
            self.memory = {}


    def apply_fixes(self, text):    

        for wrong, correct in FIXES.items():
            text = text.replace(wrong, correct)

        return text

    def translate(self, text, target_lang):

        if text is None:
            return ""

        text = str(text).strip()


        if text == "":
            return ""

        encoded = tokenizer(
            text,
            return_tensors="pt"
        ).to(self.device)

        generated = model.generate(
    **encoded,
    forced_bos_token_id=tokenizer.convert_tokens_to_ids(config.TARGET_LANG),
    max_new_tokens=80,
    num_beams=4,
    early_stopping=True,
    no_repeat_ngram_size=3,
    repetition_penalty=1.2
)

        translated = tokenizer.batch_decode(
    generated,
    skip_special_tokens=True
)[0]

        return self.apply_fixes(translated)

    def translate_preserving_separator(self, text):

        if text is None:
            return ""

        text = str(text).strip()

        if text == "":
            return ""

        # Если нет разделителя — переводим как обычно
        if "||" not in text:
            return self.translate(text)

        parts = [p.strip() for p in text.split("||")]

        translated = self.translate_batch(parts)

        return " || ".join(translated)

    def translate_batch(self, texts):

        result = [None] * len(texts)

        # Индексы одинаковых текстов
        pending = {}

        for i, text in enumerate(texts):

            if text is None:
                result[i] = ""
                continue

            text = str(text).strip()

            if text == "":
                result[i] = ""
                continue
            
            if "||" in text:
                result[i] = self.translate_preserving_separator(text)
                continue

            if text in self.cache:
                result[i] = self.cache[text]
                continue

            if text in self.memory:
                result[i] = self.memory[text]
                continue

            pending.setdefault(text, []).append(i)

        unique = list(pending.keys())

        BATCH = 16

        for start in range(0, len(unique), BATCH):

            part = unique[start:start+BATCH]

            encoded = tokenizer(
                part,
                return_tensors="pt",
                padding=True,
                truncation=True
            ).to(self.device)

            with torch.inference_mode():

                generated = model.generate(
                    **encoded,
                    forced_bos_token_id=tokenizer.convert_tokens_to_ids(config.TARGET_LANG),
                    max_new_tokens=80,
                    num_beams=4,
                    early_stopping=True,
                    no_repeat_ngram_size=3,
                    repetition_penalty=1.2
                )

            translated = tokenizer.batch_decode(
                generated,
                skip_special_tokens=True
            )

            translated = [
    self.apply_fixes(x)
    for x in translated
]
            

            original_part = unique[start:start+BATCH]

            for original, protected, dst in zip(original_part, part, translated):

                self.cache[original] = dst
                self.memory[original] = dst

                for index in pending[original]:
                    result[index] = dst

            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(
                    self.memory,
                    f,
                    ensure_ascii=False,
                    indent=4
                )

        return result


translator = LocalTranslator()