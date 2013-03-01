#!/usr/bin/env python
# encoding: utf-8

import re
import sys
import os
import time

'''
a python script to fix require modules of goog closure framework

How does it work:
1, scan paths provided by args --modules_path, and get a list of modules provided
2, scan paths provided by args --fix_path, use re to get all modules used in the file
3, if a file use a module in provided modules list(get in step1), but it doesn't provide or require it, then mark that this file miss this module

argments:
--root_path: the root path, all other path is relative to this path. if not set, it will be the current path of this scripts.
--modules_path: the path where to get all provided modules
--fix_path: the path to fix
--ignore_path: ignore path
--ignore_module: ignore module, all it's submodules will be ignored if ends with *
--mod: three mod check/fix/remove. in check mod, it will only print out errs; in fix mod, it will print and fix errs; in remove mod, it will remove all the goog.require statement generate by this tool(depend on the // autofix comment)

the args modules_path/fix_path/ignore_path can be file or dir path
you can add many modules_path/fix_path/ignore_path/ignore_module args

@example:
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

@author lhx
'''


class AutoRequire():

    def __init__(self):
        self.rootpath = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))
        self.mod = 'check'  # mod
        self.modules_path = []   # get modules provided from these paths
        self.fix_path = []   # paths to fix
        self.ignore_path = []   # paths to ignore
        self.ignore_module = []   # modules to ignore
        self.provide_re = re.compile("goog.provide\([\'\"]" + "([\w.]+)" + "[\'\"]\)")  # provide statement
        self.require_re = re.compile("goog.require\([\'\"]" + "([\w.]+)" + "[\'\"]\)")  # require  statement
        self.auto_require_re = re.compile("[\t\r\n ]*goog.require\([\'\"]" + "([\w.]+)" + "[\'\"]\)[ \t\r\n]*//[ \t]*autofix\n")  # auto require statement
        self.comment_re = re.compile('(\/\*(\s|.)*?\*\/)|(\/\/.*)')   # js comment

    def parse_provides(self, dir_path):
        '''
        get all modules provided
        '''
        dir_path = os.path.join(self.rootpath, dir_path)
        result = []
        if os.path.isdir(dir_path):
            for lists in os.listdir(dir_path):
                path = os.path.join(dir_path, lists)
                if os.path.isdir(path):
                    result.extend(self.parse_provides(path))
                else:
                    modules = self.parse_provides_(path)
                    if modules:
                        result.extend(modules)
        else:
            modules = self.parse_provides_(dir_path)
            if modules:
                result.extend(modules)
        return result

    def parse_provides_(self, path):
        if not self.ignore_(path):
            #print "parse modules:" + path
            f = open(path, 'r')
            text = self.trim_comment_(''.join(f.readlines()))
            return self.trim_ignore_module_(self.provide_re.findall(text))

    def parse_requires_(self, path):
        if not self.ignore_(path):
            f = open(path, 'r')
            text = self.trim_comment_(''.join(f.readlines()))
            return self.trim_ignore_module_(self.require_re.findall(text))

    def ignore_(self, path):
        '''
        ignore it, if in ignore_path or is not a js file
        '''
        ext = os.path.splitext(path)[1]
        if not os.path.isdir(path) and not ext == '.js':
            return True
        for ig in self.ignore_path:
            if path.startswith(os.path.join(self.rootpath, ig)):
                return True
        return False

    def trim_ignore_module_(self, modules):
        if not self.ignore_module:
            return modules
        result = []
        for m in modules:
            if not self.ignore_module_(m):
                result.append(m)
        return result

    def ignore_module_(self, module):
        for m in self.ignore_module:
            if m.endswith('*') and module.startswith(m[:-1]):
                return True
            elif m == module:
                return True
        return False

    def trim_comment_(self, text):
        return self.comment_re.sub('', text)

    def fix(self, path, modules):
        abs_path = os.path.join(self.rootpath, path)
        results = []
        if os.path.isdir(abs_path):
            for lists in os.listdir(abs_path):
                path = os.path.join(abs_path, lists)
                if os.path.isdir(path):
                    results.extend(self.fix(path, modules))
                else:
                    result = self.fix_(path, modules)
                    if result:
                        results.append(result)
        else:
            result = self.fix_(path, modules)
            if result:
                results.append(result)
        return results

    def fix_(self, path, modules):
        if self.ignore_(path):
            return
        print 'parse: ' + path
        f = open(path, 'r')
        origin_text = ''.join(f.readlines())
        text = self.trim_comment_(origin_text)
        errs = []
        require_provides = []   # 已经require或者provide的模块
        require_provides.extend(self.parse_requires_(path) or [])
        require_provides.extend(self.parse_provides_(path) or [])
        # 下面的代码注意模块和子模块的require不要重复
        for module in modules:
            if not module in require_provides:
                r = re.compile('\W(' + module + '[\w.]*)')  # 比如A.B 那么A.BC就不行，A.B.c就行
                matches = r.findall(text)
                for matched in matches:
                    for m in modules:
                        if matched.startswith(m):
                            already_required = False
                            # 是否已经处理
                            for mm in require_provides:
                                if m == mm or matched == mm or matched.startswith(mm + "."):  # 避免出现A.BC  实际只引入了A.B的bug
                                    already_required = True
                            if already_required:
                                continue
                            else:
                                errs.append(m)
                                require_provides.append(m)
                                break
        f.close()
        if len(errs):   # 有错误
            errs = sorted(errs, reverse=True)
            if self.mod == 'check':
                print '----------modules missed (%s):%s' % (len(errs), errs)
            if self.mod == 'fix':
                f = open(path, 'w')
                requires_text = '\n'.join(['goog.require(\'%s\') // autofix' % m for m in errs])
                f.write('\n'.join([requires_text, origin_text]))
                print '----------modules fixed (%s):%s' % (len(errs), errs)

            return dict(
                path=path,
                errs=errs
                )

    def remove(self, path):
        count = 0
        if self.ignore_(path):
            return count
        abs_path = os.path.join(self.rootpath, path)
        if os.path.isdir(abs_path):
            for lists in os.listdir(abs_path):
                sub_path = os.path.join(abs_path, lists)
                count += self.remove(sub_path)
        else:
            print 'parse: %s' % abs_path
            f = open(abs_path, 'r')
            origin_text = ''.join(f.readlines())
            text = ''
            text = self.auto_require_re.sub('', origin_text)
            f.close()
            f = open(abs_path, 'w')
            f.write(text)
            f.close()
            count += 1
        return count

    def run(self):
        start = time.time()
        if self.mod == 'remove':
            count = 0
            for path in self.fix_path:
                count += self.remove(path)
            end = time.time()
            print '---------------------------- %s processed, time used: %s-------------------------' % (count, end-start)
        else:
            modules = []
            for path in self.modules_path:
                modules.extend(self.parse_provides(path))
            modules = sorted(modules, key=lambda x: len(x)*-1)  # 按长度排序
            print "modules(%s):" % len(modules)
            print modules
            results = []
            for path in self.fix_path:
                results.extend(self.fix(path, modules))
            end = time.time()
            all_errs_count = 0
            for r in results:
                all_errs_count += len(r['errs'])
            print '---------------------------- %s files have err, errs count: %s , time used: %s-------------------------' % (len(results), all_errs_count, end-start)
            return results


def main():
    #解析参数
    ar = AutoRequire()
    for i, arg in enumerate(sys.argv):
        if arg == "--root_path":
            ar.rootpath = sys.argv[i+1]
        if arg == "--mod":
            ar.mod = sys.argv[i+1]
        if arg == "--modules_path":
            ar.modules_path.append(sys.argv[i+1])
        if arg == "--fix_path":
            ar.fix_path.append(sys.argv[i+1])
        if arg == "--ignore_path":
            ar.ignore_path.append(sys.argv[i+1])
        if arg == "--ignore_module":
            ar.ignore_module.append(sys.argv[i+1])
    ar.run()


if __name__ == '__main__':
    main()
