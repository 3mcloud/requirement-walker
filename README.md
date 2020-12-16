# Requirement Walker

A simple python package which makes it easy to crawl/parse/walk over the requirements within a `requirements.txt` file. It can handle nested requirement files, i.e. `-r ./nested_path/other_reqs.txt` and handle paths to local pip packages (but cannot currently parse their requirements): `./pip_package/my_pip_package # requirement-walk: local-package-name=my-package`. Comments within the requirement files can also be preserved.

## Installation

```bash
pip install requirement-walker
```

## Arguments

Arguments for `requirement-walker` are parsed from the comments within the `requirements.txt` files.

Arguments should follow the pattern of:

```python
flat-earth==1.1.1 # requirement-walker: {arg1_name}={arg1_val}
bigfoot==0.0.1 # He is real requirement-walker: {arg1_name}={arg1_val}|{arg2_name}={arg2_val1},{arg2_val2}
```

Available arguments:
| Name | Expect # of Values | Discription |
| - | -| -|
| local-package-name | 0 or 1 | If a requirement is a path to a local pip package, then provide this argument to tell the walker that its local. You can optionally tell provide the name of the pip package which can be used when filtering requirements. (See [Example Workflow](#example-workflow)) |
| root-relative | 1 | Can be provided along with `local-package-name` or can be stand alone with any `-r` requirements. When the walker sees a relative path for a requirement, it will use this provided value instead of the value actually in that line of the `requirements.txt` file when saving to a file. |

## Example Workflow

Lets walk through a complex example. Note, I am only doing the `requirement.txt` files like this to give a detailed example. I do NOT recommend you do requirements like this.

### Folder Structure

```text
walk_requirements.py
example_application
│   README.md
│   project_requirements.txt
│
└───lambdas
│   │   generic_reqs.txt
│   │
│   └───s3_event_lambda
│   │   │   s3_lambda_reqs.txt
│   │   │   ...
│   │   │
│   │   └───src
│   │       │   ...
│   │
│   └───api_lambda
│       │   api_lambda_reqs.txt
│       │   ...
│       │
│       └───src
│           │   ...
│
└───pip_packages
    └───orm_models
        │   setup.py
        │
        └───orm_models
        │   |   ...
        │
        └───tests
            |   ...
```

**NOTE:** This package CANNOT currently parse a setup.py file to walk its requirements but we can keep track of the path to the local requirement.

### walk_requirements.py

Assuming `requirement-walker` is already installed in a virtual environment or locally such that it can be imported.

These files can also be found in `./test/examples/example_application`.

```python
""" Example Script """
# Assuming I am running this script in the directory it is within above.

# Built In
import logging

# 3rd Party
from requirement_walker import RequirementFile

# Owned


if __name__ == '__main__':
    FORMAT = '[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.DEBUG)
    req_file = RequirementFile('./example_application/project_requirements.txt')
    # RequirementFile has a magic method __iter__ written for it so it can be iterated over.
    # Outputs found down below
    print("Output 1:", *req_file, sep='\n') # This will print the file basically as is
    print("---------------------------------------------")
    print("Output 2:", *req_file.iter_recursive(), sep='\n') # This will print all reqs in without -r
    # You can also send the reqs to a single file via:
    # req_file.to_single_file(path_to_output_to)
    # That method accepts, no_empty_lines and no_comment_only_lines as arguments.
```

### project_requirements.txt

```python
# One-lining just to show multiple -r works on one line, -r is the only thing that works on one line.
-r ./lambdas/s3_event_lambda/s3_lambda_reqs.txt --requirement=./lambdas/api_lambda/api_lambda_reqs.txt # comment

./pip_packages/orm_models # requirement-walker: local-package-name=orm-models
orm @ git+ssh://git@github.com/ORG/orm.git@5e2b6d14f00ffbd473dfe8b8602b79e37266568c # git link
orm2 @ git+https://github.com/ORG/orm2.git@5e2b6d14f00ffbd473dfe8b8602b79e37266568c # git link
orm3 @ git+http://github.com/ORG/orm3.git@5e2b6d14f00ffbd473dfe8b8602b79e37266568c # git link
```

### generic_reqs.txt

```python
moto==1.3.16.dev67
pytest==6.1.2
pytest-cov==2.10.1
pylint==2.6.0
docker==4.4.0
coverage==4.5.4
# Some other stuff

# Add empty line
```

### s3_lambda_reqs.txt

```python
-r ./../generic_reqs.txt
./../../pip_packages/orm_models # requirement-walker: local-package-name|root-relative=./pip_packages/orm_models
```

### api_lambda_reqs.txt

```python
-r ./../generic_reqs.txt
./../../pip_packages/orm_models # requirement-walker: local-package-name|root-relative=./pip_packages/orm_models
```

### Output

```text
... Logs omitted ...
Output 1:
# One-lining just to show multiple -r works on one line, -r is the only thing that works on one line.
-r C:\Users\{UserName}\Repos\3mcloud\requirement-walker\tests\examples\example_application\lambdas\s3_event_lambda\s3_lambda_reqs.txt # comment
-r C:\Users\{UserName}\Repos\3mcloud\requirement-walker\tests\examples\example_application\lambdas\api_lambda\api_lambda_reqs.txt # comment

./pip_packages/orm_models # requirement-walker: local-package-name=orm-models
orm@ git+ssh://git@github.com/ORG/orm.git@5e2b6d14f00ffbd473dfe8b8602b79e37266568c # git link
orm2@ git+https://github.com/ORG/orm2.git@5e2b6d14f00ffbd473dfe8b8602b79e37266568c # git link
orm3@ git+http://github.com/ORG/orm3.git@5e2b6d14f00ffbd473dfe8b8602b79e37266568c # git link
---------------------------------------------
Output 2:
# One-lining just to show multiple -r works on one line, -r is the only thing that works on one line.
moto==1.3.16.dev67
pytest==6.1.2
pytest-cov==2.10.1
pylint==2.6.0
docker==4.4.0
coverage==4.5.4
# Some other stuff

# Add empty line
./pip_packages/orm_models # requirement-walker: local-package-name|root-relative=./pip_packages/orm_models
moto==1.3.16.dev67
pytest==6.1.2
pytest-cov==2.10.1
pylint==2.6.0
docker==4.4.0
coverage==4.5.4
# Some other stuff

# Add empty line
./pip_packages/orm_models # requirement-walker: local-package-name|root-relative=./pip_packages/orm_models

./pip_packages/orm_models # requirement-walker: local-package-name=orm-models
orm@ git+ssh://git@github.com/ORG/orm.git@5e2b6d14f00ffbd473dfe8b8602b79e37266568c # git link
orm2@ git+https://github.com/ORG/orm2.git@5e2b6d14f00ffbd473dfe8b8602b79e37266568c # git link
orm3@ git+http://github.com/ORG/orm3.git@5e2b6d14f00ffbd473dfe8b8602b79e37266568c # git link
```

**NOTE**: Duplicates are NOT filtered out. You can do this on your own if you want using `entry.requirement.name` to filter them out as you iterate.

## Failed Parsing

Sometimes the requirement parser fails. For example, maybe it tries parsing a `-e` or maybe you do a local pip package but don't provide `local-package-name`. If this happens, please open an issue; however, you should still be able to code yourself around the issue or use the walker till a fix is implemented. The walker aims to store as much information as it can, even in cases of failure. See the following example.

### requirements.txt

```python
astroid==2.4.2
attrs==20.3.0
aws-xray-sdk==2.6.0
boto==2.49.0
./local_pips/my_package # This will cause a failed requirement step
boto3==1.16.2
botocore==1.19.28
certifi==2020.11.8
cffi==1.14.4
./pip_packages/orm_models # requirement-walker: local-package-name
```

### Code

```python
""" Example Script """

# Built In
import logging

# 3rd Party
from requirement_walker import RequirementFile

# Owned

if __name__ == '__main__':
    FORMAT = '[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.DEBUG)
    entries = RequirementFile('./requirements.txt')
    print(*entries, sep='\n')
```

### Code Output

```text
... logs omitted ...
astroid==2.4.2
attrs==20.3.0
aws-xray-sdk==2.6.0
boto==2.49.0
./local_pips/my_package # This will cause a failed requirement step
boto3==1.16.2
botocore==1.19.28
certifi==2020.11.8
cffi==1.14.4
./pip_packages/orm_models # requirement-walker: local-package-name
```

Note that it still printed correctly, but if you look at the logs you will see what happened:

```text
WARNING  requirement_walker.walker:walker.py:148 Unable to parse requirement. Doing simple FailedRequirement where name=failed_req and url=./local_pips/my_package. Open Issue in GitHub to have this fixed.
```

If you want, you can refine requirements by looking at class instances:

```python
""" Example Script """

# Built In
import logging

# 3rd Party
from requirement_walker import RequirementFile, LocalPackageRequirement, FailedRequirement

# Owned

if __name__ == '__main__':
    FORMAT = '[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.ERROR)
    for entry in RequirementFile('./requirements.txt'):
        # `requirement` can be one of: `None, FailedRequirement, LocalPackageRequirement`
        if isinstance(entry.requirement, FailedRequirement):
            print("This requirement was a failed req.", entry)
        elif isinstance(entry.requirement, LocalPackageRequirement):
            print("This requirement was a local req.", entry)
        # If a entry is a requirement file, `requirement` will be None
        # and `requirement_file` will have a value other then None.
        elif isinstance(entry.requirement_file, RequirementFile):
            print("This entry is another requirement file.", entry)
# Ouput:
# This requirement was a failed req. ./local_pips/my_package # This will cause a failed requirement step
# This requirement was a local req. ./pip_packages/orm_models # requirement-walker: local-package-name
```

## What is an Entry?

We define an entry as a single line within a requirements.txt file which consists of a requirement file this line could be empty, only have a comment, only have a requirement, be a reference to another requirement file, or have a mixture of a requirement/requirement file and a comment.

An Entry object has four main attributes but will not have them all at the same time: `comment: Union[Comment, None]`, `requirement: Union[pkg_resources.Requirement, FailedRequirement, LocalPackageRequirement, None]`, `proxy_requirement: Union[_ProxyRequirement, None]`, and lasty `requirement_file: [RequirementFile, None]`. If all of these attributes are set to `None` then the line the entry represents was an empty line. The `requirement` has a value then `proxy_requirement` will as well but `requirement_file` will NOT. If `requirement_file` has a value then `requirement` and `proxy_requirement` will NOT. A `comment` can exist on its own (a line with only a comment) or a comment can exist with either `requirement` or `requirement_file`.

Note, you will mainly work with `requirement` NOT `proxy_requirement`, but there may be cases where the package does not behave properly, in which cases it `proxy_requirement` will hold all the other information pulled by the walker.
