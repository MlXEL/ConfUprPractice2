import argparse
import os
import sys
from urllib.parse import urlparse
import gzip
import urllib.request
from io import StringIO

try:
    import yaml
except ImportError:
    print("Ошибка: требуется библиотека PyYAML. Установите ее: pip install pyyaml")
    sys.exit(2)


DEFAULT_CONFIG = "config_valid.yaml"


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
    # Проверить как путь
    if os.path.exists(val):
        return
    # Проверить как URL
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


def extract_dependencies(packages_content, package_name):
    """
    Извлекает прямые зависимости указанного пакета из содержимого файла Packages.
    """
    lines = iter(packages_content.splitlines())
    current_package = None
    depends_line = None

    for line in lines:
        line = line.strip()

        if line.startswith("Package: "):
            current_package = line[len("Package: "):].strip()
            depends_line = None
        elif line.startswith("Depends: ") and current_package == package_name:
            depends_line = line[len("Depends: "):].strip()
            break

    if not depends_line:
        return []

    # Разбор Depends: pkg1, pkg2 (>= ver), pkg3
    dependencies = []
    for dep in depends_line.split(','):
        dep = dep.strip()
        # Убираем версии и прочее
        dep = dep.split()[0]
        if dep:
            dependencies.append(dep)

    return dependencies


def get_repo_packages_content(repo_url):
    """
    Скачивает и возвращает содержимое файла Packages или Packages.gz из репозитория.
    """
    packages_url = repo_url.rstrip('/') + '/Packages'
    gz_url = packages_url + '.gz'

    try:
        response = urllib.request.urlopen(gz_url)
        content = gzip.decompress(response.read()).decode('utf-8')
        return content
    except Exception:
        try:
            response = urllib.request.urlopen(packages_url)
            return response.read().decode('utf-8')
        except Exception as e:
            raise ValueError(f"Не удалось получить файл Packages: {e}")


def main():
    parser = argparse.ArgumentParser(description="Минимальный прототип визуализации зависимостей (Этап 2).")
    parser.add_argument("-c", "--config", default=DEFAULT_CONFIG, help="Путь к YAML-конфигу")
    args = parser.parse_args()

    try:
        cfg = load_config(args.config)
    except Exception as e:
        print(f"Ошибка загрузки конфигурации: {e}")
        sys.exit(1)

    try:
        # Валидация параметров
        package_name = cfg.get("package_name")
        validate_string(package_name, "package_name")

        repo_url = cfg.get("repository")
        validate_url_or_path(repo_url, "repository")

        mode = validate_mode(cfg.get("mode"), "mode")

        output_image = cfg.get("output_image")
        validate_string(output_image, "output_image")
        if "." not in output_image:
            raise ValueError("output_image должно содержать расширение файла.")

        max_depth = validate_int(cfg.get("max_depth"), "max_depth", minimum=0, maximum=100)

    except Exception as e:
        print(f"Ошибка валидации конфигурации: {e}")
        sys.exit(2)

    # Параметры для вывода
    params = {
        "package_name": package_name,
        "repository": repo_url,
        "mode": mode,
        "output_image": output_image,
        "max_depth": max_depth,
    }

    print("Параметры конфигурации:")
    print_kv(params)

    print("\nЭтап 1: вывод параметров выполнен успешно.\n")

    # === ЭТАП 2: сбор данных ===
    print("Этап 2: Сбор данных")

    try:
        packages_content = get_repo_packages_content(repo_url)
        dependencies = extract_dependencies(packages_content, package_name)

        if dependencies:
            print(f"Прямые зависимости пакета '{package_name}':")
            for dep in dependencies:
                print(f"- {dep}")
        else:
            print(f"У пакета '{package_name}' нет зависимостей или он не найден в репозитории.")

    except Exception as e:
        print(f"Ошибка при получении зависимостей: {e}")
        sys.exit(3)

    print("\nЭтап 2: сбор данных выполнен успешно.")


if __name__ == "__main__":
    main()