import argparse
import os
import sys
from urllib.parse import urlparse

try:
    import yaml
except Exception:
    print("Ошибка: требуется библиотека PyYAML. Установите ее: pip install pyyaml")
    sys.exit(2)


DEFAULT_CONFIG = "config.yaml"


def load_config(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Файл конфигурации не найден: {path}")
    with open(path, "r", encoding="utf-8") as f:
        try:
            cfg = yaml.safe_load(f)
        except Exception as e:
            raise ValueError(f"Ошибка парсинга YAML: {e}")
    if cfg is None:
        raise ValueError("Файл конфигурации пуст.")
    return cfg


def validate_string(value, name):
    if value is None:
        raise ValueError(f"Параметр '{name}' отсутствует.")
    if not isinstance(value, str):
        raise ValueError(f"Параметр '{name}' должен быть строкой.")
    if value.strip() == "":
        raise ValueError(f"Параметр '{name}' не должен быть пустым.")


def validate_url_or_path(value, name):
    if value is None:
        raise ValueError(f"Параметр '{name}' отсутствует.")
    if not isinstance(value, str) or value.strip() == "":
        raise ValueError(f"Параметр '{name}' должен быть непустой строкой.")
    val = value.strip()
    #Проверить как путь
    if os.path.exists(val):
        return
    #Проверить как URL
    parsed = urlparse(val)
    if parsed.scheme and parsed.netloc:
        return
    raise ValueError(f"Параметр '{name}' не является существующим путем или корректным URL: {val}")


def validate_mode(value, name):
    if value is None:
        raise ValueError(f"Параметр '{name}' отсутствует.")
    if not isinstance(value, str):
        raise ValueError(f"Параметр '{name}' должен быть строкой ('test' или 'repo').")
    val = value.strip().lower()
    if val not in ("test", "repo"):
        raise ValueError(f"Параметр '{name}' должен иметь значение 'test' или 'repo'.")
    return val


def validate_int(value, name, minimum=0, maximum=None):
    if value is None:
        raise ValueError(f"Параметр '{name}' отсутствует.")
    if isinstance(value, int):
        n = value
    else:
        #Попытка привести строку к int
        try:
            n = int(value)
        except Exception:
            raise ValueError(f"Параметр '{name}' должен быть целым числом.")
    if n < minimum:
        raise ValueError(f"Параметр '{name}' должен быть >= {minimum}.")
    if maximum is not None and n > maximum:
        raise ValueError(f"Параметр '{name}' должен быть <= {maximum}.")
    return n


def print_kv(params):
    for k in sorted(params.keys()):
        print(f"{k}: {params[k]}")


def main():
    parser = argparse.ArgumentParser(description="Минимальный прототип визуализации зависимостей (Этап 1).")
    parser.add_argument("-c", "--config", default=DEFAULT_CONFIG, help="Путь к YAML-конфигу")
    args = parser.parse_args()

    try:
        cfg = load_config(args.config)
    except Exception as e:
        print(f"Ошибка загрузки конфигурации: {e}")
        sys.exit(1)

    try:
        #package_name
        validate_string(cfg.get("package_name"), "package_name")

        #repository (URL или путь)
        validate_url_or_path(cfg.get("repository"), "repository")

        #mode: 'test' or 'repo'
        mode = validate_mode(cfg.get("mode"), "mode")

        #output_image — имя файла (строка)
        validate_string(cfg.get("output_image"), "output_image")
        #Проверить расширение
        out_name = cfg.get("output_image").strip()
        if "." not in out_name:
            raise ValueError("output_image должно содержать расширение файла, например 'graph.png'.")

        #max_depth — целое >=0
        max_depth = validate_int(cfg.get("max_depth"), "max_depth", minimum=0, maximum=100)

    except Exception as e:
        print(f"Ошибка валидации конфигурации: {e}")
        sys.exit(2)

    #Параметры для печати
    params = {
        "package_name": cfg.get("package_name"),
        "repository": cfg.get("repository"),
        "mode": mode,
        "output_image": out_name,
        "max_depth": max_depth,
    }

    #Вывести все параметры в формате ключ-значение
    print("Параметры конфигурации:")
    print_kv(params)

    print("\nЭтап 1: вывод параметров выполнен успешно.")


if __name__ == "__main__":
    main()
