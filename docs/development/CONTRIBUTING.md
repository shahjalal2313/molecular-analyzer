# Contributing to Molecular Analyzer

First off, thank you for considering contributing to Molecular Analyzer! It's people like you that make open source such a great community.

## Where do I go from here?

If you've noticed a bug or have a feature request, [make one](https://github.com/shahjalal2313/molecular-analyzer/issues/new)! It's generally best if you get confirmation of your bug or approval for your feature request this way before starting to code.

### Fork & create a branch

If this is something you think you can fix, then [fork the repository](https://github.com/shahjalal2313/molecular-analyzer/fork) and create a branch with a descriptive name.

A good branch name would be (where issue #38 is the ticket you're working on):

```bash
git checkout -b 38-add-feature-x
```

### Get the test suite running

Make sure you're running the test suite locally before you start making changes.

```bash
pytest
```

### Implement your fix or feature

At this point, you're ready to make your changes! Feel free to ask for help; everyone is a beginner at first 😸

### Make a Pull Request

At this point, you should switch back to your main branch and make sure it's up to date with the latest upstream version of the repository.

```bash
git remote add upstream git@github.com:shahjalal2313/molecular-analyzer.git
git checkout main
git pull upstream main
```

Then update your feature branch from your local copy of main, and push it!

```bash
git checkout 38-add-feature-x
git rebase main
git push --set-upstream origin 38-add-feature-x
```

Finally, go to GitHub and [make a Pull Request](https://github.com/shahjalal2313/molecular-analyzer/compare)

### Keeping your Pull Request updated

If a maintainer asks you to "rebase" your PR, they're saying that a lot of code has changed, and that you need to update your branch so it's easier to merge.

To learn more about rebasing and merging, check out this guide from Atlassian: [https://www.atlassian.com/git/tutorials/merging-vs-rebasing](https://www.atlassian.com/git/tutorials/merging-vs-rebasing)