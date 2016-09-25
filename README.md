# pretix-cartshare

pretix plugin that allows you to prepare a cart and share it with a customer.


## Development setup

1. Make sure that you have a working
   [pretix development setup](https://docs.pretix.eu/en/latest/development/setup.html).

2. Clone this repository. I prefer to clone it *inside* my pretix repository at ``/local/pretix-cartshare``. This is
   not a submodule, just a second repository cloned within the working directory of the first one, but ignored by the
   first outer repository. This is not really pretty, but in my experiences it eases some tasks in terms of tooling
   and IDE support.

3. Activate the virtual environment you use for pretix development.

4. Execute ``python setup.py develop`` within this directory to register this application with pretix's plugin registry.

5. Restart your local pretix server. You can now use the plugins from this repository for your events!
