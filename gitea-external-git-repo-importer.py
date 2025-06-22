import os
import subprocess
import sys
import re


def run_command(command, error_message, dry_run=False):
    """Runs a shell command, with optional dry run support."""
    if dry_run:
        print(f"[DRY RUN] Command: {command}")
        return
    try:
        # Using capture_output to prevent subprocess from printing directly
        # We can print it ourselves if needed for debugging.
        result = subprocess.run(
            command, check=True, shell=True, text=True, capture_output=True
        )
        if result.stdout:
            print(f"[CMD] STDOUT: {result.stdout.strip()}")
        if result.stderr:
            print(f"[CMD] STDERR: {result.stderr.strip()}")
    except subprocess.CalledProcessError as e:
        print(f"Error: {error_message}\nCommand: {e.cmd}\n")
        print(f"Stderr: {e.stderr}")
        sys.exit(1)


def parse_git_url(url):
    """
    Parses a Gitea or other Git provider URL to extract domain, owner, and repo name.

    :param url: The Git repository URL.
    :return: (domain, owner, repo_name) tuple.
    """
    # Regex for git@domain:owner/repo.git format
    ssh_pattern_1 = r"git@(?P<domain>[\w.-]+):(?P<owner>[\w-]+)/(?P<repo>[\w.-]+)\.git"
    # Regex for ssh://git@domain/owner/repo.git format
    ssh_pattern_2 = r"ssh://git@(?P<domain>[\w.-]+(?::\d+)?)/(?P<owner>[\w-]+)/(?P<repo>[\w.-]+)\.git"
    # Regex for https://domain/owner/repo format (allowing .git at the end)
    http_pattern = r"https?://(?P<domain>[\w.-]+(?::\d+)?)/(?P<owner>[\w-]+)/(?P<repo>[\w.-]+?)(?:\.git)?$"

    if match := re.match(ssh_pattern_1, url):
        return match.group("domain"), match.group("owner"), match.group("repo")
    elif match := re.match(ssh_pattern_2, url):
        return match.group("domain"), match.group("owner"), match.group("repo")
    elif match := re.match(http_pattern, url):
        return match.group("domain"), match.group("owner"), match.group("repo")
    else:
        print(f"Error: Invalid Git repository URL: {url}")
        sys.exit(1)


def check_or_create_gitea_repo(gitea_repo_url, private=False, org=None, dry_run=False):
    """
    Checks if a Gitea repository exists and creates it if it doesn't.

    :param gitea_repo_url: URL of the Gitea repository.
    :param private: Boolean indicating if the repository should be private.
    :param org: Organization under which to create the repository.
    :param dry_run: Whether to perform a dry run.
    """
    _, owner, repo_name = parse_git_url(gitea_repo_url)

    # If an org is specified, it becomes the owner. Otherwise, it's the logged-in user.
    # 'tea' handles this based on the owner in the repo string.
    repo = f"{org}/{repo_name}" if org else f"{owner}/{repo_name}"

    # Check if the repository exists
    print(f"Checking if the repository {repo} exists on Gitea...")
    repo_check_command = f"tea repo {repo}"
    result = subprocess.run(repo_check_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode == 0:
        print(f"Repository {repo} already exists.")
        return

    # Create the repository if it doesn't exist
    print(f"Creating Gitea repository: {repo}")
    visibility_flag = "--private" if private else "--public"
    create_command = f"tea repo create --name {repo_name} {visibility_flag}"
    # Specify the owner only if it's an organization
    if org:
        create_command += f" --owner {org}"

    run_command(create_command, f"Failed to create Gitea repository: {repo}", dry_run)


def archive_repository(gitea_repo_url, dry_run=False):
    """Archives a Gitea repository."""
    _, owner, repo_name = parse_git_url(gitea_repo_url)
    repo_full_name = f"{owner}/{repo_name}"
    print(f"CLI does not currently support archiving (https://gitea.com/gitea/tea/issues/454). Skipping...")
    # print(f"Archiving repository: {repo_full_name}")
    # tea uses 'repo edit --archived=true'
    # archive_command = f"tea repo edit --archived=true {repo_full_name}"
    # run_command(archive_command, f"Failed to archive repository: {repo_full_name}", dry_run)


def import_repository(external_repo_url, gitea_repo_url, private=False, org=None, archive=False, dry_run=False):
    """
    Imports an external Git repository into a new Gitea repository.

    :param external_repo_url: URL of the external Git repository.
    :param gitea_repo_url: URL of the Gitea repository.
    :param private: Boolean indicating if the repository should be private.
    :param org: Organization under which to create the repository.
    :param archive: Whether to archive the repository after importing.
    :param dry_run: Whether to perform a dry run.
    """
    check_or_create_gitea_repo(gitea_repo_url, private=private, org=org, dry_run=dry_run)

    repo_name_from_url = external_repo_url.split("/")[-1].replace(".git", "")
    temp_clone_dir = f"{repo_name_from_url}.git"

    print(f"\n=== Importing repository: {repo_name_from_url} ===")
    print(f"Cloning {external_repo_url} into a temporary bare repository...")
    run_command(f"git clone --bare {external_repo_url}", f"Failed to clone repository: {external_repo_url}", dry_run)

    if not dry_run:
        os.chdir(temp_clone_dir)

    print(f"Pushing mirror to Gitea at {gitea_repo_url}...")
    run_command(f"git push --mirror {gitea_repo_url}", f"Failed to push repository to Gitea: {gitea_repo_url}", dry_run)

    if not dry_run:
        os.chdir("..")
        print("Cleaning up temporary local repository...")
        run_command(f"rm -rf {temp_clone_dir}", f"Failed to remove temporary local repository: {temp_clone_dir}")

    if archive:
        archive_repository(gitea_repo_url, dry_run)


def process_repositories(repo_list, private=False, org=None, archive=False, dry_run=False):
    """
    Processes a list of repositories.

    :param repo_list: A list of tuples containing external and Gitea repo URLs.
    :param private: Whether repositories should be private.
    :param org: Organization under which to create the repositories.
    :param archive: Whether to archive repositories after importing.
    :param dry_run: Whether to perform a dry run.
    """
    for external_repo_url, gitea_repo_url in repo_list:
        import_repository(
            external_repo_url, gitea_repo_url, private=private, org=org, archive=archive, dry_run=dry_run
        )


def main():
    # Pre-flight check for 'tea' and login status
    try:
        result = subprocess.run("tea login whoami", shell=True, check=True, text=True, capture_output=True)
        print(f"--- Successfully authenticated to Gitea as: {result.stdout.strip()} ---")
    except subprocess.CalledProcessError:
        print("Error: Gitea CLI 'tea' not found or you are not logged in.")
        print("Please install 'tea' and run 'tea login add ...' to configure access to your Gitea instance.")
        sys.exit(1)

    print("\nThis script imports external Git repositories to your Gitea instance.")
    print("Provide repositories via a file with each line containing two URLs separated by a space:")
    print("Example: https://github.com/some/external.git https://your.gitea.com/new-owner/new-repo.git")
    file_path = input("Enter the file path: ").strip()

    if not os.path.isfile(file_path):
        print("Error: File not found. Please provide a valid file path.")
        sys.exit(1)

    private = input("\nFor Gitea repositories that don't exist, should they be made private? (yes/no): ").strip().lower() == "yes"
    org = input("For repositories that don't exist, enter the Gitea organization (leave blank for your personal account): ").strip() or None
    archive = input("Archive repositories on Gitea after successful import? (yes/no): ").strip().lower() == "yes"
    dry_run = input("Enable dry run mode? (This will print commands but not execute them) (yes/no): ").strip().lower() == "yes"

    try:
        with open(file_path, "r") as file:
            repo_list = [line.strip().split() for line in file if line.strip() and not line.strip().startswith("#")]
    except Exception as e:
        print(f"Error: Could not read the file. {e}")
        sys.exit(1)

    for pair in repo_list:
        if len(pair) != 2:
            print(f"Error: Invalid line format: {pair}. Each line must have exactly two URLs.")
            sys.exit(1)

    print("\nThe following actions will be performed:")
    for external, gitea in repo_list:
        print(f"- Import {external} -> {gitea}")
        if archive:
            print(f"  -> Then archive {gitea}")

    if not dry_run:
        confirm = input("\nDo you want to proceed? (yes/no): ").strip().lower()
        if confirm not in ["yes", "y"]:
            print("Operation canceled.")
            sys.exit(0)

    process_repositories(repo_list, private=private, org=org, archive=archive, dry_run=dry_run)
    print("\nImport process finished.")


if __name__ == "__main__":
    main()
