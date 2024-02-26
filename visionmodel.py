import base64
import io
import os
import requests

from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image
import torch
from transformers import VisionEncoderDecoderModel, ViTImageProcessor, AutoTokenizer


class VisionModelFactory:
    def __init__(self):
        pass

    def create(self, model_str, device=None):
        """
        Creates and returns a vision model based on the provided model string and device.

        Args:
            model_str (str): The model string specifying the type of vision model to create.
            device (str, optional): The device type to use for model inference.

        Returns:
            VisionModel: A vision model based on the provided model string and device.
        """
        if model_str != "openai":
            return HuggingfaceVisionModel(model_str, device)
        else:
            return OpenaiVisionModel()


class HuggingfaceVisionModel:
    def __init__(self, model_str, device=None):
        """
        Initializes the VisionEncoderDecoderModel with the specified model string.

        Args:
            model_str (str): The model string to initialize the VisionEncoderDecoderModel.
            device (torch.device, optional): The device to use for the model. Defaults to None.

        Returns:
            None
        """

        self.model = VisionEncoderDecoderModel.from_pretrained(model_str)
        self.feature_extractor = ViTImageProcessor.from_pretrained(model_str)
        self.tokenizer = AutoTokenizer.from_pretrained(model_str)

        self.device = device
        if self.device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

    def predict(self, images, **kwargs):
        """
        Predict captions for a list of images using the model.

        Args:
            images (list): A list of PIL.Image objects.
            **kwargs: Additional keyword arguments for the model's generate method.

        Returns:
            list: A list of predicted captions for the input images.
        """

        for image in images:
            if not isinstance(image, Image.Image):
                raise ValueError("All images must be of type PIL.Image")

            if image.mode != "RGB":
                image = image.convert(mode="RGB")

        pixel_values = self.feature_extractor(
            images=images, return_tensors="pt"
        ).pixel_values
        pixel_values = pixel_values.to(self.device)

        if not kwargs:
            kwargs = {"max_length": 128, "num_beams": 4}

        outputs = self.model.generate(pixel_values, **kwargs)
        captions = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)
        del pixel_values

        return captions


class OpenaiVisionModel:
    def __init__(self):
        """
        Initializes the class instance with a new OpenAI model.
        """
        load_dotenv()

    def predict(self, images, detail="low"):
        """
        Perform image captioning on the input images using the provided model and tokenizer.

        Args:
            images (List[Image]): A list of PIL.Image objects representing the input images.
            **kwargs: Additional keyword arguments to customize the image captioning process, such as "max_length" and "num_beams".

        Returns:
            List[str]: A list of generated captions for the input images.
        """

        def pil_image_to_base64(pil_image):
            """
            Convert a PIL image to a base64 encoded string.

            :param pil_image: A PIL image object
            :return: A base64 encoded string
            """
            buffered = io.BytesIO()
            pil_image.save(buffered, format="JPEG")
            return base64.b64encode(buffered.getvalue()).decode("utf-8")

        captions = []
        # OpenAI only supports 1 image at a time.  If you pass it multiple images, it will use all of them
        # to generate a single caption.
        for image in images:
            if not isinstance(image, Image.Image):
                raise ValueError("All images must be of type PIL.Image")

            image_data = pil_image_to_base64(image)
            #import pdb; pdb.set_trace()

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
            }

            payload = {
                "model": "gpt-4-vision-preview",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "What’s in this image?"},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                },
                                "detail": f"{detail}",
                            },
                        ],
                    }
                ],
                "max_tokens": 300,
            }

            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            captions.append(response.json()["choices"][0]["message"]["content"].strip())

        return captions
