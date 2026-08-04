# Wilfred

Wilfred is a public and extensible Butler runtime.

This repository contains reusable runtime components, contracts, the plugin
SDK, documentation and public plugins.

Private entities, integrations, secrets and operational configuration belong
in separate consumer repositories such as Alfred.

## Bootstrap

    PYTHONPATH=src python -m wilfred

## Tests

    PYTHONPATH=src python -m unittest discover -s tests -v
