# Nylas Production Python library

This library provides logging and other functions used in our production
infrastructure.

## Installation

This library is available on pypi. You can install it by running `pip install nylas-production-python`.

## Contributing

We'd love your help making Nylas better. We hang out on Slack. [Join the channel here ![Slack Invite Button](http://slack-invite.nylas.com/badge.svg)](http://slack-invite.nylas.com) You can also email [support@nylas.com](mailto:support@nylas.com).

Please sign the [Contributor License Agreement](https://nylas.com/cla.html) before submitting pull requests. (It's similar to other projects, like NodeJS or Meteor.)

If you have access to the PyPI repository, you can make a new release as such:

```shell
python setup.py test
python setup.py release <major/minor/patch>
git log # to verify
python setup.py publish
```

Also, don't forget to `git push --tags` to update the release tags on GitHub.

