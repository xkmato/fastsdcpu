# FastSD CPU API Documentation

This documentation describes the REST API for FastSD CPU. The API allows you to programmatically generate images, upscale them, and manage configurations.

By default, the API server runs on `http://localhost:8000`.

Interactive Swagger documentation is available at `http://localhost:8000/api/docs`.

---

## 1. Image Generation

### `POST /api/generate`
The primary endpoint for generating images (Text-to-Image and Image-to-Image).

**Request Body (`LCMDiffusionSetting`):**

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `prompt` | `string` | `""` | The description of the image you want to generate. |
| `negative_prompt` | `string` | `""` | What you want to exclude from the image. |
| `image_height` | `int` | `512` | Image height in pixels. |
| `image_width` | `int` | `512` | Image width in pixels. |
| `inference_steps` | `int` | `1` | Number of denoising steps. |
| `guidance_scale` | `float` | `1.0` | How closely the model follows the prompt. |
| `number_of_images` | `int` | `1` | Number of images to generate. |
| `seed` | `int` | `123123` | Random seed for reproducibility. |
| `use_openvino` | `bool` | `false` | Use OpenVINO for faster inference on Intel hardware. |
| `diffusion_task` | `string` | `"text_to_image"` | `"text_to_image"` or `"image_to_image"`. |
| `init_image` | `string` | `null` | Base64 encoded image for Image-to-Image tasks. |
| `strength` | `float` | `0.6` | Image-to-Image transformation strength (0.0 to 1.0). |
| `controlnet` | `object` | `null` | ControlNet settings (see below). |

**ControlNet Object:**

| Field | Type | Description |
| :--- | :--- | :--- |
| `enabled` | `bool` | Enable ControlNet. |
| `adapter_path` | `string` | Path to the ControlNet model. |
| `conditioning_scale` | `float` | Strength of the control (0.0 to 1.0). |
| `image` | `string` | **Base64 encoded** control/hint image. |

**Response (`StableDiffusionResponse`):**
```json
{
  "images": ["base64_string_1", "..."],
  "latency": 5.23,
  "error": ""
}
```

---

## 2. Image Upscaling

### `POST /api/upscale`
Upscale an existing image using various models.

**Request Body (`UpscaleRequest`):**

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `image` | `string` | (Required) | **Base64 encoded** source image. |
| `upscale_mode` | `string` | `"normal"` | `"normal"` (EDSR 2x), `"sd_upscale"` (Stable Diffusion), or `"aura_sr"` (AURA-SR 4x). |
| `strength` | `float` | `0.3` | Transformation strength (only used for `sd_upscale`). |

**Response:** Same as `/api/generate`.

---

## 3. Image Variations

### `POST /api/image-variations`
A simplified endpoint for generating variants of an existing image.

**Request Body:**
```json
{
  "image": "base64_encoded_image_string",
  "strength": 0.4
}
```

**Response:** Same as `/api/generate`.

---

## 4. Metadata and Configuration

### `GET /api/info`
Returns system information including device type, OS, and CPU details.

### `GET /api/models`
Returns lists of all available:
- LCM LoRA models
- Stable Diffusion models
- OpenVINO models
- LCM models

### `GET /api/config`
Returns the current active application settings, including generation defaults and file paths.

### `POST /api/settings`
Update global application settings.

**Request Body:** A complete `Settings` object (matching the output of `GET /api/config`).

---

## 5. Examples

### Generating an image with Python
```python
import requests
import base64

payload = {
    "prompt": "A beautiful sunset over the mountains",
    "use_openvino": True,
    "number_of_images": 1
}

response = requests.post("http://localhost:8000/api/generate", json=payload)
data = response.json()

if not data["error"]:
    img_data = base64.b64decode(data["images"][0])
    with open("output.jpg", "wb") as f:
        f.write(img_data)
```
