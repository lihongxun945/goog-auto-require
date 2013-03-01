#goog-auto-require

#What is this?
it is a python scripts can check the miss require statement in your google closure project,
and it can event auto fix the errs.
if you  use google closure lib in your js, then it may be helpfull to you.

##How does it work:
1. scan paths provided by args --modules_path, and get a list of modules provided
2. scan paths provided by args --fix_path, use re to get all modules used in the file
3. if a file use a module in provided modules list(get in step1), but it doesn't provide or require it, then mark that this file miss this module

##argments:
you can use these args:
* --root_path: the root path, all other path is relative to this path. if not set, it will be the current path of this scripts.
* --modules_path: the path where to get all provided modules
* --fix_path: the path to fix
* --ignore_path: ignore path
* --ignore_module: ignore module, all it's submodules will be ignored if ends with *
* --mod: three mod check/fix/remove. in check mod, it will only print out errs; in fix mod, it will print and fix errs; in remove mod, it will remove all the goog.require statement generate by this tool(depend on the // autofix comment)

the args modules_path/fix_path/ignore_path can be file or dir path  
you can add many modules_path/fix_path/ignore_path/ignore_module args

##example:
    python scripts/goog_auto_require.py
        --root_path ~/zhihu/zhihu/
        --modules_path static/js/v2/
        --modules_path static/js/google-closure-library/closure
        --fix_path static/js/v2/
        --ignore_path static/js/v2/deps.js
        --ignore_path static/js/v2/tests
        --ignore_module goog.i18n.*
        --ignore_module ZH
        --mod fix

##author
@author lhx

