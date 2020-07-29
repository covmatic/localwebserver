# Introduction

The protocol files that you can upload to your OT-2s will be kept here.

In order to avoid errors running local protocol simulations add the ./custom_defaults/*.json files to your ~/.opentrons folder.

How simulate opentrons protocol on Windows, OS X or Linux:

$ opentrons_simulate <my_protocol_filename.py>

If you want to execute the protocol on the robot you can use:

$ opentrons_execute <path_protocol>/<protocol_name.py>

