pretix-cartshare
================

.. image:: https://img.shields.io/pypi/v/pretix-cartshare.svg
   :target: https://pypi.python.org/pypi/pretix-cartshare

.. image:: https://travis-ci.org/pretix/pretix-cartshare.svg?branch=master
   :target: https://travis-ci.org/pretix/pretix-cartshare

.. image:: https://coveralls.io/repos/github/pretix/pretix-cartshare/badge.svg?branch=master
   :target: https://coveralls.io/r/pretix/pretix-cartshare

`pretix`_ plugin that allows you to prepare a cart and share it with a customer.

Contributing
------------

If you like to contribute to this project, you are very welcome to do so. If you have any
questions in the process, please do not hesitate to ask us.

Please note that we have a `Code of Conduct`_ in place that applies to all project contributions, including issues,
pull requests, etc.

Development setup
^^^^^^^^^^^^^^^^^

1. Make sure that you have a working `pretix development setup`_.

2. Clone this repository. I prefer to clone it *inside* my pretix repository at ``/local/pretix-cartshare``. This is
   not a submodule, just a second repository cloned within the working directory of the first one, but ignored by the
   first outer repository. This is not really pretty, but in my experiences it eases some tasks in terms of tooling
   and IDE support.

3. Activate the virtual environment you use for pretix development.

4. Execute ``python setup.py develop`` within this directory to register this application with pretix's plugin registry.

5. Restart your local pretix server. You can now use the plugin from this repository for your events!

5. Execute ``make`` within this directory to compile translations.

6. Restart your local pretix server. You can now use the plugin from this repository for your events by enabling it in
   the 'plugins' tab in the settings.

License
-------

Copyright 2016 Raphael Michel

Released under the terms of the Apache License 2.0

.. _pretix development setup: https://docs.pretix.eu/en/latest/development/setup.html
.. _Code of Conduct: https://docs.pretix.eu/en/latest/development/contribution/codeofconduct.html
.. _pretix: https://github.com/pretix/pretix
