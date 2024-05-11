if __name__ == "__main__":
    import argparse

    import celery

    import src.config.celery

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode",
        type=str,
        choices=["worker", "flower", "beat", "healthcheck"],
        help="Celery mode to run.",
    )
    parser.add_argument(
        "--loglevel",
        type=str,
        choices=["debug", "info", "warning", "error", "critical"],
        default="info",
        help="Celery log level.",
    )
    args = parser.parse_args()

    celery_conf = src.config.celery.get_celery_setting()

    if args.mode == "worker" and celery_conf.sentry.is_sentry_available(mode="celery"):
        import sentry_sdk

        sentry_sdk.init(**celery_conf.sentry.build_config(mode="celery"))

    celery_app = celery.Celery()
    celery_app.config_from_object(celery_conf)
    celery_app.set_default()

    loglevel = f"--loglevel={args.loglevel}"
    match (celery_mode := args.mode):
        case "worker":
            celery_app.worker_main(argv=["worker", loglevel])
        case "flower" | "beat":
            celery_app.start(argv=[celery_mode, loglevel])
        case "healthcheck":
            celery_app.start(argv=["inspect", "ping"])
