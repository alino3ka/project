import argparse
import ast
import csv
import sys
from pathlib import Path


class Visitor(ast.NodeVisitor):
    def __init__(self, fname, writer):
        self.fname = fname
        self.writer = writer

    def _write(self, name, node):
        self.writer.writerow([name, node.lineno, node.col_offset + 1, self.fname])

    def visit_Name(self, node):
        self._write(node.id, node)
        self.generic_visit(node)

    def visit_Call(self, node):
        for keyword in node.keywords:
            self._visit_keyword(keyword)
        self.generic_visit(node)

    def _visit_keyword(self, node):
        if node.arg:
            self._write(node.arg, node)

    def visit_Attribute(self, node):
        self.generic_visit(node)
        self._write(node.attr, node)

    def visit_Import(self, node):
        for alias in node.names:
            self._visit_alias(alias)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            for part in node.module.split("."):
                if part:
                    self._write(part, node)
        for alias in node.names:
            self._visit_alias(alias)
        self.generic_visit(node)

    def _visit_alias(self, node):
        if node.name:
            for part in node.name.split("."):
                if part:
                    self._write(part, node)
        if node.asname:
            self._write(node.asname, node)

    def visit_MatchAs(self, node):
        self._write(node.name, node)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self._write(node.name, node)
        self._visit_arguments(node.args)
        self.generic_visit(node)

    def _visit_arguments(self, args):
        for arg in args.posonlyargs:
            self._visit_arg(arg)
        for arg in args.args:
            self._visit_arg(arg)
        self._visit_arg(args.vararg)
        for default in args.defaults:
            if default is not None:
                self.visit(default)
        for arg in args.kwonlyargs:
            self._visit_arg(arg)
        for default in args.kw_defaults:
            if default is not None:
                self.visit(default)
        self._visit_arg(args.kwarg)

    def _visit_arg(self, arg):
        if not arg:
            return
        self._write(arg.arg, arg)

    def visit_Global(self, node):
        for name in node.names:
            self._write(name, node)
        self.generic_visit(node)

    def visit_Nonlocal(self, node):
        for name in node.names:
            self._write(name, node)
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        self._write(node.name, node)
        for keyword in node.keywords:
            self._visit_keyword(keyword)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self._write(node.name, node)
        self._visit_arguments(node.args)
        self.generic_visit(node)


def process_file(fname, writer):
    with fname.open() as f:
        contents = f.read()
    try:
        root = ast.parse(contents, fname)
    except SyntaxError:
        print(f"Syntax error in {fname}, ignoring", file=sys.stderr)
        return
    visitor = Visitor(fname, writer)
    visitor.visit(root)


def main():
    if len(sys.argv) not in (2, 3):
        print(f"usage: {sys.argv[0]} <path> [out.csv]", file=sys.stderr)
        sys.exit(1)
    root = Path(sys.argv[1])
    if len(sys.argv) == 3:
        out = Path(sys.argv[2]).open("w", newline="")
    else:
        out = sys.stdout
    try:
        writer = csv.writer(out)
        writer.writerow(["name", "line", "column", "file"])
        for fname in root.rglob("*.py"):
            if fname.is_file():
                process_file(fname, writer)
                print(f"Processed {fname}", file=sys.stderr)
    finally:
        if out != sys.stdout:
            out.close()

if __name__ == "__main__":
    main()
