.. _uqmethod:

UQ methods
==========
.. automodule:: uqmethod.uqmethod

Baseclass
---------
.. autoclass:: uqmethod.uqmethod.UqMethod
   :members: SetupLevels,RunSimulation

MLMC
----
.. autoclass:: uqmethod.uqmethodmlmc.Mlmc
   :members: SetupLevels,GetNodesAndWeights,PrepareAllSimulations,RunAllBatches,PrepareAllPostprocessing,RunAllBatchesPostprocessing,GetNewNCurrentSamples

Stochastic Collocation
----------------------
.. autoclass:: uqmethod.uqmethodsc.Sc
    :members: SetupLevels,InitLoc,GetNodesAndWeights,PrepareAllSimulations,RunAllBatches,GetNewNSamples
