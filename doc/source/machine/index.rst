.. _machine:

Machines
========
.. automodule:: machine.machine

Baseclass
---------
.. autoclass:: machine.machine.Machine

Local
-----
.. autoclass:: machine.machinelocal.Local
    :members: RunBatch ,SubmitJob ,AllocateResources

Cray
-----
.. autoclass:: machine.machinecray.Cray
    :members: RunBatch ,GenerateJob ,SubmitJob ,MonitorJob, AllocateResources
