import streamlit as st
import requests

# Set page config
st.set_page_config(page_title="OneClick Demo", page_icon="🏠", layout="wide", initial_sidebar_state="expanded")

# Application Header
st.title("README Generator")
st.markdown("This application generates a README file for your GitHub project.")

# Input for GitHub Repo URL
github_repo_url = st.text_input("GitHub Repository URL", "")

# Function to Generate README
def generate_readme(github_repo_url):
    # Function to extract owner and repo name from URL
    def extract_repo_details(url):
        parts = url.split('/')
        owner = parts[-2]
        repo = parts[-1]
        return owner, repo

    # Extracting owner and repo name
    owner, repo = extract_repo_details(github_repo_url)

    # GitHub API endpoint to get repo details
    api_url = f"https://api.github.com/repos/{owner}/{repo}"

    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()

        # Extracting information
        language = data.get('language', 'Not specified')
        stars = data.get('stargazers_count', 0)
        forks = data.get('forks_count', 0)
        issues = data.get('open_issues_count', 0)

        # Formatting README content
        readme_content = f"# {repo}\n\n"
        readme_content += f"**Primary Language**: {language}\n"
        readme_content += f"**Stars**: {stars}\n"
        readme_content += f"**Forks**: {forks}\n"
        readme_content += f"**Open Issues**: {issues}\n"

        return readme_content

    except requests.RequestException as e:
        return f"Error: {e}"

# Generate README Button
if st.button("Generate README"):
    readme = generate_readme(github_repo_url)
    if readme:
        st.markdown("Generated README:")
        st.code(readme, language='markdown')

# Footer
st.markdown("---")
st.markdown("© 2024 [OneClick](https://one-click.dev)")
