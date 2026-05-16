#!/usr/bin/env python3
"""Command-line interface for the notes utility."""

import argparse
import sys

import notes as note_store


def fmt(note: dict) -> str:
    tags = f"  [{', '.join(note['tags'])}]" if note["tags"] else ""
    return f"[{note['id']}] {note['text']}{tags}  ({note['created_at'][:10]})"


def cmd_add(args: argparse.Namespace) -> None:
    tags = [t.strip() for t in args.tags.split(",")] if args.tags else []
    note = note_store.add(args.text, tags)
    print(f"Added note #{note['id']}")


def cmd_list(args: argparse.Namespace) -> None:
    all_notes = note_store.list_all()
    if not all_notes:
        print("No notes yet.")
        return
    for n in all_notes:
        print(fmt(n))


def cmd_search(args: argparse.Namespace) -> None:
    results = note_store.search(args.keyword)
    if not results:
        print(f"No notes matching '{args.keyword}'.")
        return
    for n in results:
        print(fmt(n))


def cmd_tag(args: argparse.Namespace) -> None:
    results = note_store.filter_by_tag(args.tag)
    if not results:
        print(f"No notes tagged '{args.tag}'.")
        return
    for n in results:
        print(fmt(n))


def cmd_delete(args: argparse.Namespace) -> None:
    if note_store.delete(args.id):
        print(f"Deleted note #{args.id}")
    else:
        print(f"No note with id {args.id}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Simple CLI note manager")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="Add a new note")
    p_add.add_argument("text", help="Note text")
    p_add.add_argument("--tags", help="Comma-separated tags", default="")
    p_add.set_defaults(func=cmd_add)

    p_list = sub.add_parser("list", help="List all notes")
    p_list.set_defaults(func=cmd_list)

    p_search = sub.add_parser("search", help="Search notes by keyword")
    p_search.add_argument("keyword", help="Keyword to search for")
    p_search.set_defaults(func=cmd_search)

    p_tag = sub.add_parser("tag", help="List notes with a specific tag")
    p_tag.add_argument("tag", help="Tag to filter by")
    p_tag.set_defaults(func=cmd_tag)

    p_del = sub.add_parser("delete", help="Delete a note by ID")
    p_del.add_argument("id", type=int, help="Note ID")
    p_del.set_defaults(func=cmd_delete)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
