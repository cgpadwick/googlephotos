import argparse
import io
import os

from matplotlib import pyplot as plt

from pathlib import Path

from PIL import Image

from transformers import VisionEncoderDecoderModel, ViTImageProcessor, AutoTokenizer
import torch


def caption_images(image_dir, force_cpu=False):
    """
    Captions images in the specified image directory.

    Args:
        image_dir: A string representing the directory containing the images to be captioned.

    Returns:
        None
    """

    model = VisionEncoderDecoderModel.from_pretrained(
        "nlpconnect/vit-gpt2-image-captioning"
    )
    feature_extractor = ViTImageProcessor.from_pretrained(
        "nlpconnect/vit-gpt2-image-captioning"
    )
    tokenizer = AutoTokenizer.from_pretrained("nlpconnect/vit-gpt2-image-captioning")

    max_length = 128
    num_beams = 4
    gen_kwargs = {"max_length": max_length, "num_beams": num_beams}

    if force_cpu:
        device = "cpu"
    else:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    for image_file in os.listdir(image_dir):
        image = Image.open(image_dir / Path(image_file))
        if image.mode != "RGB":
            image = image.convert(mode="RGB")

        pixel_values = feature_extractor(
            images=[image], return_tensors="pt"
        ).pixel_values
        pixel_values = pixel_values.to(device)

        output_ids = model.generate(pixel_values, **gen_kwargs)

        preds = tokenizer.batch_decode(output_ids, skip_special_tokens=True)
        preds = [pred.strip() for pred in preds]

        plt.imshow(image)
        plt.title(preds[0])
        plt.show()
        del pixel_values


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--imagedir",
        required=True,
        type=Path,
        help="location where the images will be read from",
    )
    parser.add_argument(
        "--forcecpu",
        required=False,
        type=int,
        default=None,
        help="force the predicition to occur on the CPU",
    )

    args = parser.parse_args()

    if not args.imagedir.exists():
        raise ValueError(f"Invalid path specified: {args.imagedir}")

    caption_images(args.imagedir, force_cpu=args.forcecpu)
