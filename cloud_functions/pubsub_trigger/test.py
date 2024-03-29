from dotenv import load_dotenv
import main

url = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"
load_dotenv()

caption = main.predict_from_url(url)

print(caption)


