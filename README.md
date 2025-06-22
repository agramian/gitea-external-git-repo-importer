# Gitea External Git Repo Importer

A Python script to automate the import of external Git repositories into Gitea, with support for creating destination repositories on-the-fly using the Gitea CLI.

The script uses the procedure described in the official GitHub doc for [Importing an external Git repository using the command line](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/importing-an-external-git-repository-using-the-command-line)

## Features
- Imports multiple external Git repositories into Gitea.
- Automatically creates the destination repositories if they don’t exist.
- Supports private repositories and organization accounts.
- Cleans up temporary files after import.

*Note: archiving repositories after import is supported in the script arguments but not functional because 
it is [not supported via the Gitea CLI yet](https://gitea.com/gitea/tea/issues/454).*

## Requirements
- [Gitea CLI (`tea`)](https://gitea.com/gitea/tea) installed and authenticated.
- Python 3.7+.
- Git installed.

## Usage
1. Make sure the Gitea CLI is authenticated:

        gitea login add

1. Prepare a file listing the external and Gitea repositories, one pair per line (ex: `external_repo_url gitea_repo_url`).
   
   Example `repositories.txt`:

        https://external-host.com/extuser/repo1.git https://gitea.com/user/repo1.git
        https://external-host.com/extuser/repo2.git https://gitea.com/orgname/repo2.git
        ssh://git@external-host.com/extuser/repo3.git ssh://git@gitea.com/user/repo3.git
        # If the "ssh://" prefix is not included on the url,
        # note the different separator (":" vs "/") after the domain.
        git@external-host.com:extuser/repo4.git git@gitea.com:user/repo4.git

1. Run the script

        python gitea-external-git-repo-importer.py

    *Note: some systems may require explicitly using `python3` to ensure Python 3 is used to run the script.*
1. Follow the prompts:
   - Enter the file path for the repositories list.
   - Specify whether to make the Gitea repositories private.
   - Optionally, provide the name of the Gitea organization.
   - Specify whether to archive the Gitea repositories after import (*currently not functional).
   - Specify whether to execute the script in dry mode to preview the actions.
1. Output:
   - Repositories imported to Gitea.
   - Temporary local files cleaned up.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
