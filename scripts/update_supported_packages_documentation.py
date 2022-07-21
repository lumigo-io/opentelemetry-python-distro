import os
from src.ci.tested_versions_utils import generate_support_matrix_markdown

project_root = os.path.dirname(os.path.dirname(__file__))

readme_content = []
with (open(os.path.join(project_root, "README.md"), "r")) as readme:
    readme_content = readme.readlines()

# Find the beginning of the "Supported packages" section
supported_packages_start_index = readme_content.index("## Supported packages\n")
next_section_start_index = None

for count, line in enumerate(readme_content[supported_packages_start_index + 2 :]):
    if line.startswith("## "):
        next_section_start_index = supported_packages_start_index + 2 + count
        break

if not next_section_start_index:
    raise Exception("No next section found")

updated_readme_content = readme_content[: supported_packages_start_index + 1]
updated_readme_content += ["\n"]
updated_readme_content += [
    line + "\n" for line in generate_support_matrix_markdown("src/lumigo_opentelemetry")
]
updated_readme_content += ["\n"]
updated_readme_content += readme_content[next_section_start_index:]

with (open(os.path.join(project_root, "README.md"), "w")) as readme:
    readme.writelines(updated_readme_content)
