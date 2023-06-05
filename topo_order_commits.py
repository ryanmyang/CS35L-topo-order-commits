import os
import sys
import zlib
import pathlib


class CommitNode:
    def __init__(self, commit_hash):
        self.commit_hash = commit_hash
        self.parents = []
        self.children = []


def find_git_directory():
    current_dir = os.getcwd()
    print("\n", current_dir)

    while True:
        if os.path.exists(os.path.join(current_dir, '.git')):
            # print("found .git in " + str(current_dir), file=sys.stderr)
            return current_dir

        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:
            break

        current_dir = parent_dir

    print("Not inside a Git repository" + str(current_dir), file=sys.stderr)
    sys.exit(1)


def build_commit_graph(git_directory, branches):
    refs_directory = os.path.join(git_directory, '.git', 'refs', 'heads')
    objects_directory = os.path.join(git_directory, '.git', 'objects')

    commit_graph = {}
    root_commits = set()

    # Retrieve branch names and their corresponding commit hashes
    branch_commits = {}
    # Set branch_commits to dictionary of branches and their commits


    # Traverse each branch to build commit graph
    for branch_id, branch_name in branches.items():
        visited = set()
        stack = [branch_id]

        while stack:
            commit_hash = stack.pop()
            if commit_hash in visited:
                continue

            visited.add(commit_hash)

            # Create CommitNode if not already present in commit graph
            if commit_hash not in commit_graph:
                commit_graph[commit_hash] = CommitNode(commit_hash)

            current_node = commit_graph[commit_hash]

            # Retrieve commit object and its parent hashes
            object_path = os.path.join(
                objects_directory, commit_hash[:2], commit_hash[2:])
            with open(object_path, 'rb') as f:
                compressed_data = f.read()

            decompressed_data = zlib.decompress(
                compressed_data).decode('utf-8')
            lines = decompressed_data.splitlines()

            # Extract parent hashes from commit object
            parent_hashes = [line.split(' ')[1]
                             for line in lines if line.startswith('parent')]

            # Update parent-child relationships in the commit graph
            for parent_hash in parent_hashes:
                if parent_hash not in commit_graph:
                    commit_graph[parent_hash] = CommitNode(parent_hash)
                parent_node = commit_graph[parent_hash]

                parent_node.children.append(commit_hash)
                current_node.parents.append(parent_hash)

                stack.append(parent_hash)
            # Check if current commit is a root commit
            if len(current_node.parents) == 0:
                root_commits.add(commit_hash)

    return commit_graph, root_commits


def get_local_branches(git_directory):
    refs_directory = pathlib.Path(git_directory) / '.git' / 'refs' / 'heads'

    branches = {}

    for branch_path in refs_directory.rglob('*'):
        if branch_path.is_file() and branch_path.name != ".DS_Store":
            relative_path = branch_path.relative_to(refs_directory)
            with open(branch_path, 'r') as f:
                branch_id = f.read().strip()
                branches.setdefault(branch_id, []).append(str(relative_path))

    return branches


def get_topological_order(commit_graph, root_commits):
    visited = []
    order = []
    stack = []

    # Perform depth-first search starting from each root commit
    for root_commit in root_commits:
        stack.append(root_commit)

        while stack:
            commit_hash = stack[-1]

            # Traverse children first
            for child_hash in commit_graph[commit_hash].children:
                if child_hash not in visited:
                    stack.append(child_hash)
                    break
            else:
                # All children have been visited
                commit_hash = stack.pop()
                visited.append(commit_hash)
                order.append(commit_hash)

    no_dupes = []
    [no_dupes.append(x) for x in order if x not in no_dupes]
    return no_dupes


def print_commit_order(commit_order, commit_graph, branch_names):
    prev = None

    for commit_hash in commit_order:
        commit_node = commit_graph[commit_hash]

        # Check if a sticky end needs to be inserted
        # "If the next commit to be printed is not the parent of the current commit, insert a "sticky end""
        # The “sticky end” will contain the commit hashes of the parents of the current commit
        if prev and commit_hash not in commit_graph[prev].parents:
            print(" ".join(commit_graph[prev].parents) + " =", end="\n\n")
            sticky_start = "= " + " ".join(commit_node.children)
            print(sticky_start)

        # Print the commit hash
        print(commit_hash, end=" ")

        # Print branch names if the commit corresponds to a branch head
        if commit_hash in branch_names:
            branches = sorted(branch_names[commit_hash])
            print(" ".join(branches), end="")

        print()

        # Update sticky end and reset sticky start
        prev = commit_hash


def topo_order_commits():
    git_directory = find_git_directory()
    branches = get_local_branches(git_directory)
    graph, roots = build_commit_graph(git_directory, branches)
    topological_order = get_topological_order(graph, roots)
    print_commit_order(topological_order, graph, branches)


if __name__ == "__main__":
    # CHANGE OF DIRECTORY FOR TESTING PURPOSES
    # target_dir = "/Users/ryanmacpro/Documents/School/CS35L/Assignment6/RocketProjectatUCLA"
    target_dir = "/Users/ryanmacpro/Documents/School/CS35L/Assignment6/topo-ordered-commits-test-suite/tests/repo_fixture/example-repo-8/"

    os.chdir(target_dir)
    ########
    topo_order_commits()
