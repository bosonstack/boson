import json
import yaml
import sys
from jsonschema import validate, Draft202012Validator, exceptions

CONFIG_PATH = "/app/worker/worker.yaml"
SCHEMA_PATH = "/app/worker-config-schema.json"

def main():
    try:
        with open(CONFIG_PATH, "r") as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Failed to load worker config: {e}")
        sys.exit(1)

    try:
        with open(SCHEMA_PATH, "r") as f:
            schema = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load worker config schema: {e}")
        sys.exit(1)

    try:
        validator = Draft202012Validator(schema)
        validator.validate(config)
        print("✅ Worker config is valid.")
    except exceptions.ValidationError as e:
        print(f"❌ Worker config is invalid with error: {e.message}")
        sys.exit(1)

if __name__ == "__main__":
    main()
