from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# path to your checkpoint

# load tokenizer from base T5 (checkpoint lacks tokenizer files)
tokenizer = AutoTokenizer.from_pretrained("t5-small")
model = AutoModelForSeq2SeqLM.from_pretrained(model_path)

# test text with training prefix
text = "stance: COVID vaccine causes microchips"

# encode + generate
inputs = tokenizer(text, return_tensors="pt", truncation=True)
outputs = model.generate(**inputs, max_length=20)

# decode
prediction = tokenizer.decode(outputs[0], skip_special_tokens=True)
print("RAW MODEL OUTPUT:", prediction)



