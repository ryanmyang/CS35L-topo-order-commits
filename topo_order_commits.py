import os
import sys
import zlib

class CommitNode:
    def __init__(self, commit_hash):
        self.commit_hash = commit_hash
        self.parents = set()
        self.children = set()


def find_git_directory():
    current_dir = os.getcwd()
    print("\n",current_dir)

    while True:
        if os.path.exists(os.path.join(current_dir, '.git')):
            print("found .git in " + str(current_dir), file=sys.stderr)
            return current_dir

        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:
            break

        current_dir = parent_dir

    print("Not inside a Git repository" + str(current_dir), file=sys.stderr)
    sys.exit(1)


def build_commit_graph(git_directory):
    refs_directory = os.path.join(git_directory, '.git', 'refs', 'heads')
    objects_directory = os.path.join(git_directory, '.git', 'objects')

    commit_graph = {}
    root_commits = set()

    # Retrieve branch names and their corresponding commit hashes
    branch_commits = {}
    # Set branch_commits to dictionary of branches and their commits
    for root, _, files in os.walk(refs_directory):
        for file in files:
            branch_path = os.path.join(root, file)
            with open(branch_path, 'r') as f:
                branch_name = file
                commit_hash = f.read().strip()
                branch_commits[branch_name] = commit_hash

    # Traverse each branch to build commit graph
    for branch_name, branch_head in branch_commits.items():
        visited = set()
        stack = [branch_head]

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
            object_path = os.path.join(objects_directory, commit_hash[:2], commit_hash[2:])
            with open(object_path, 'rb') as f:
                compressed_data = f.read()

            decompressed_data = zlib.decompress(compressed_data).decode('utf-8')
            lines = decompressed_data.splitlines()

            # Extract parent hashes from commit object
            parent_hashes = [line.split(' ')[1] for line in lines if line.startswith('parent')]

            # Update parent-child relationships in the commit graph
            for parent_hash in parent_hashes:
                if parent_hash not in commit_graph:
                    commit_graph[parent_hash] = CommitNode(parent_hash)
                parent_node = commit_graph[parent_hash]

                parent_node.children.add(commit_hash)
                current_node.parents.add(parent_hash)

                stack.append(parent_hash)
            # Check if current commit is a root commit
            if len(current_node.parents) == 0:
                root_commits.add(commit_hash)

    return commit_graph, root_commits


def get_local_branches(git_directory):
    refs_directory = os.path.join(git_directory, '.git', 'refs', 'heads')

    branch_names = []
    for root, _, files in os.walk(refs_directory):
        for file in files:
            if not all(c in '0123456789abcdef' for c in file):
                continue
            branch_path = os.path.join(root, file)
            with open(branch_path, 'r') as f:
                branch_name = f.read().strip()
                branch_names.append(branch_name)

    return branch_names

def explain_directories():
    print("The 'refs' directory contains references to different Git objects, such as branches and tags.")
    print("The 'objects' directory stores the actual Git objects, such as blobs, trees, and commits.")

if __name__ == "__main__":
    # CHANGE OF DIRECTORY FOR TESTING PURPOSES
    target_dir = "/Users/ryanmacpro/Documents/School/CS35L/Assignment6/RocketProjectatUCLA"
    os.chdir(target_dir)
    ########
    git_directory = find_git_directory()
    branch_names = get_local_branches(git_directory)
    graph, roots = build_commit_graph(git_directory)
    print("Local Branches:", branch_names)
    print("Commit Graph:", graph)
    print("Roots:", roots)

    explain_directories()
