import argparse
import textwrap
import os

import visionmodel

from dotenv import load_dotenv
from matplotlib import pyplot as plt
from openai import OpenAI

from pathlib import Path
from PIL import Image
from tqdm import tqdm
from transformers import VisionEncoderDecoderModel, ViTImageProcessor, AutoTokenizer
import torch


def format_caption(caption):
    """
    Line wraps the caption.

    Args:
        caption: A string representing the caption.

    Returns:
        A string representing the formatted caption.
    """

    wrapped = textwrap.wrap(caption, width=200)
    return "\n".join(wrapped)


def caption_images(
    image_dir, output_dir, model_str="openai", device="gpu", showimages=False
):
    """
    Captions images in the specified image directory.

    Args:
        image_dir: A string representing the directory containing the images to be captioned.

    Returns:
        None
    """

    factory = visionmodel.VisionModelFactory()
    model = factory.create(model_str=model_str, device=device)

    for image_file in tqdm(os.listdir(image_dir)):
        image = Image.open(image_dir / Path(image_file))

        caption = model.predict([image])

        plt.figure(figsize=(20, 20))
        plt.imshow(image)
        plt.title(format_caption(caption[0]))
        if showimages:
            plt.show()

        plt.savefig(output_dir / Path(image_file))
        plt.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--imagedir",
        required=True,
        type=Path,
        help="location where the images will be read from",
    )
    parser.add_argument(
        "--model",
        required=True,
        type=str,
        help="the model to use for image captioning.  Use openai or a huggingface model id, e.g. nlpconnect/vit-gpt2-image-captioning",
    )
    parser.add_argument(
        "--outputdir",
        required=True,
        type=Path,
        help="location where the images and captions will be saved",
    )
    parser.add_argument(
        "--device",
        required=False,
        type=str,
        default="cuda",
        help="device to use for local prediction",
    )
    parser.add_argument(
        "--show",
        required=False,
        type=int,
        default=1,
        help="show the image with the generated caption in a window",
    )

    args = parser.parse_args()

    if not args.imagedir.exists():
        raise ValueError(f"Invalid path specified: {args.imagedir}")

    if not args.outputdir.exists():
        raise ValueError(f"Invalid path specified: {args.outputdir}")

    caption_images(
        args.imagedir,
        args.outputdir,
        model_str=args.model,
        device=args.device,
        showimages=args.show,
    )
