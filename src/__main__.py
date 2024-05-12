import uvicorn

import src.config.fastapi

if __name__ == "__main__":
    config_obj = src.config.fastapi.get_fastapi_setting()
    uvicorn.run(
        "src:create_app",
        factory=True,
        **config_obj.to_uvicorn_config(),
    )
