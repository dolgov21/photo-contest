from app.web.app import start_app

if __name__ == "__main__":
    try:
        start_app("etc/config.yaml")
    except KeyboardInterrupt:
        pass
