import platform

import uvicorn
from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware

from backend.api.models.response import StableDiffusionResponse
from backend.api.models.upscale import UpscaleRequest
from backend.base64_image import base64_image_to_pil, pil_image_to_base64_str
from backend.device import get_device_name
from backend.models.device import DeviceInfo
from backend.models.lcmdiffusion_setting import DiffusionTask, LCMDiffusionSetting
from backend.upscale.upscaler import upscale_image
from constants import APP_VERSION, DEVICE
from context import Context
from models.interface_types import InterfaceType
from models.settings import Settings
from state import get_settings
from paths import FastStableDiffusionPaths
import uuid
import os

app_settings = get_settings()
app = FastAPI(
    title="FastSD CPU",
    description="Fast stable diffusion on CPU",
    version=APP_VERSION,
    license_info={
        "name": "MIT",
        "identifier": "MIT",
    },
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)
print(app_settings.settings.lcm_diffusion_setting)
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
context = Context(InterfaceType.API_SERVER)


@app.get("/api/")
async def root():
    return {"message": "Welcome to FastSD CPU API"}


@app.get(
    "/api/info",
    description="Get system information",
    summary="Get system information",
)
async def info():
    device_info = DeviceInfo(
        device_type=DEVICE,
        device_name=get_device_name(),
        os=platform.system(),
        platform=platform.platform(),
        processor=platform.processor(),
    )
    return device_info.model_dump()


@app.get(
    "/api/config",
    description="Get current configuration",
    summary="Get configurations",
)
async def config():
    return app_settings.settings


@app.get(
    "/api/models",
    description="Get available models",
    summary="Get available models",
)
async def models():
    return {
        "lcm_lora_models": app_settings.lcm_lora_models,
        "stable_diffusion": app_settings.stable_diffsuion_models,
        "openvino_models": app_settings.openvino_lcm_models,
        "lcm_models": app_settings.lcm_models,
    }


@app.post(
    "/api/generate",
    description="Generate image(Text to image,Image to Image)",
    summary="Generate image(Text to image,Image to Image)",
)
async def generate(diffusion_config: LCMDiffusionSetting) -> StableDiffusionResponse:
    app_settings.settings.lcm_diffusion_setting = diffusion_config
    if diffusion_config.diffusion_task == DiffusionTask.image_to_image:
        app_settings.settings.lcm_diffusion_setting.init_image = base64_image_to_pil(
            diffusion_config.init_image
        )

    if diffusion_config.controlnet:
        if isinstance(diffusion_config.controlnet, list):
            for cn in diffusion_config.controlnet:
                if cn.enabled and cn.image:
                    cn._control_image = base64_image_to_pil(cn.image)
        else:
            if diffusion_config.controlnet.enabled and diffusion_config.controlnet.image:
                diffusion_config.controlnet._control_image = base64_image_to_pil(
                    diffusion_config.controlnet.image
                )

    images = context.generate_text_to_image(app_settings.settings)

    if images:
        images_base64 = [pil_image_to_base64_str(img) for img in images]
    else:
        images_base64 = []
    return StableDiffusionResponse(
        latency=round(context.latency, 2),
        images=images_base64,
        error=context.error,
    )


@app.post(
    "/api/upscale",
    description="Upscale an image",
    summary="Upscale image",
)
async def upscale(upscale_request: UpscaleRequest) -> StableDiffusionResponse:
    try:
        source_image = base64_image_to_pil(upscale_request.image)
        # We need a temp file for the upscaler logic which currently uses paths
        temp_input_path = f"temp_{uuid.uuid4()}.png"
        temp_output_path = f"temp_upscaled_{uuid.uuid4()}.png"
        source_image.save(temp_input_path)

        images = upscale_image(
            context=context,
            src_image_path=temp_input_path,
            dst_image_path=temp_output_path,
            upscale_mode=upscale_request.upscale_mode.value,
            strength=upscale_request.strength,
        )

        images_base64 = [pil_image_to_base64_str(img) for img in images]

        if os.path.exists(temp_input_path):
            os.remove(temp_input_path)
        if os.path.exists(temp_output_path):
            os.remove(temp_output_path)

        return StableDiffusionResponse(
            latency=0,  # upscale_image doesn't currently return latency in a simple way
            images=images_base64,
        )
    except Exception as e:
        return StableDiffusionResponse(
            latency=0,
            images=[],
            error=str(e),
        )


@app.post(
    "/api/image-variations",
    description="Generate image variations",
    summary="Image variations",
)
async def image_variations(
    image: str = Body(..., embed=True),
    strength: float = Body(0.4, embed=True),
) -> StableDiffusionResponse:
    app_settings.settings.lcm_diffusion_setting.init_image = base64_image_to_pil(image)
    app_settings.settings.lcm_diffusion_setting.strength = strength
    app_settings.settings.lcm_diffusion_setting.prompt = ""
    app_settings.settings.lcm_diffusion_setting.negative_prompt = ""
    app_settings.settings.lcm_diffusion_setting.diffusion_task = (
        DiffusionTask.image_to_image.value
    )

    images = context.generate_text_to_image(app_settings.settings)

    if images:
        images_base64 = [pil_image_to_base64_str(img) for img in images]
    else:
        images_base64 = []
    return StableDiffusionResponse(
        latency=round(context.latency, 2),
        images=images_base64,
        error=context.error,
    )


@app.post(
    "/api/settings",
    description="Update application settings",
    summary="Update settings",
)
async def update_settings(settings: Settings):
    app_settings.settings.lcm_diffusion_setting = settings.lcm_diffusion_setting
    app_settings.settings.generated_images = settings.generated_images
    app_settings.save()
    return {"message": "Settings updated successfully"}


def start_web_server(port: int = 8000):
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
    )
