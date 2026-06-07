import torch
import open_clip
from PIL import Image

device = "cpu"

model, preprocess, _ = open_clip.create_model_and_transforms(
    "ViT-B-32",
    pretrained="laion2b_s34b_b79k"
)

model = model.to(device)

tokenizer = open_clip.get_tokenizer("ViT-B-32")

labels = [
    "a real photograph",
    "an AI generated image",
    "a computer generated artwork"
]

text = tokenizer(labels).to(device)


def predict_image(image_path):

    image = Image.open(image_path).convert("RGB")
    image = preprocess(image).unsqueeze(0).to(device)

    with torch.no_grad():

        image_features = model.encode_image(image)
        text_features = model.encode_text(text)

        image_features /= image_features.norm(dim=-1, keepdim=True)
        text_features /= text_features.norm(dim=-1, keepdim=True)

        similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)

        values, indices = similarity[0].topk(1)

    label = labels[indices[0]]

    if "real" in label:
        return "Real Photo", float(values[0]) * 100
    else:
        return "AI Generated", float(values[0]) * 100