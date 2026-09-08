import React, { useState, useRef } from 'react';
import { api } from '../../services/api';
import { sound } from '../../audio/soundEngine';

interface TwoStreamUploadViewProps {
  onRunCommand?: (cmd: string) => void;
  onClose?: () => void;
}

const SAMPLE_LEDGER_CSV = "txid,timestamp,input_addresses,output_addresses,input_amounts,output_amounts,fee_btc,script_type,scenario_id\n156686565,2016-08-07 14:26:11,\"[\"\"1Awg2jyQSht5DXTnMB5d53wgW7RAEamG\"\", \"\"1tNRGVoahTgCe96jiEeKTmmbbp89z\"\"]\",\"[\"\"1h5QvPBsQVeYheDV6BwF3W7DL2vBX\"\"]\",\"[0.01688925, 0.00175668]\",[0.01822274],0.00042319,P2WPKH,sample_ransomware_campaign\n506784234,2016-08-07 14:26:11,\"[\"\"1h5QvPBsQVeYheDV6BwF3W7DL2vBX\"\"]\",\"[\"\"1ZdMGsxaDPnGUZPvCH8sWj5ZYcs66w\"\"]\",[0.01822274],[0.01798583],0.00023691,P2PKH,sample_ransomware_campaign\n758883601,2016-08-07 14:26:11,\"[\"\"1ZdMGsxaDPnGUZPvCH8sWj5ZYcs66w\"\"]\",\"[\"\"159AMGmaAsa6RFuNj7iMN9ntJPhTip45k6\"\"]\",[0.01798583],[0.01794007],4.576e-05,P2PKH,sample_ransomware_campaign\n179262906,2015-07-21 05:30:43,\"[\"\"1CXFBDpTuaLQXX8rENriUC8zJfd8mGC\"\"]\",\"[\"\"1oaRZpfiSTKMorEiPCv6mWNse25gL\"\", \"\"1B5B9EjL9u2CAx5DALAYKKqArBRje\"\", \"\"1R7RopEKg2tKkg3FGk2sAZXGbfGNC\"\"]\",[0.00647458],\"[0.00112425, 0.00154365, 0.00341259]\",0.00039409,P2WPKH,sample_layering_network\n629099363,2015-07-21 05:30:43,\"[\"\"1oaRZpfiSTKMorEiPCv6mWNse25gL\"\"]\",\"[\"\"17gpHuZqA9gf9QEaj6jhvgLpBZQ\"\", \"\"1Q1ifdAeRzUU1wvLeofhYSJ4frkKW\"\", \"\"1PbbWdKLeHEkvLtKF8f9BKnVeciZLWxGV\"\", \"\"1fN91WxySVZ1Zj51CXScB9dg7suaPyJ\"\", \"\"1mfTT7iHfoQmCCHx1mm4xGx3hMTU238Uj\"\"]\",[0.00112425],\"[0.00017906, 7.406e-05, 1.201e-05, 0.00018174, 0.00024584]\",0.00043154,P2WSH,sample_layering_network\n683433672,2015-07-21 05:30:43,\"[\"\"1B5B9EjL9u2CAx5DALAYKKqArBRje\"\"]\",\"[\"\"1ZbosnydtedJ9yG1Y7rbutXwhVW\"\", \"\"1uwUZsfGNsnQqEpC7PAnUDgTKP\"\", \"\"1Fw9gLtg4GtkQ4ZwXjBQ6uFsUfK6LxX\"\", \"\"1hjGtk5KGzEhnfJEMYg8dVzAZtPYwr\"\", \"\"1LXPLTCWKtRnA94V3kgRD6QY23uZL8igwu\"\", \"\"1uzq8nBm1e5dxsArYSYiq9Hky3dDwcFQ\"\", \"\"1afGPa5zW7kEG8G2okaXVtYzX5X\"\"]\",[0.00154365],\"[0.00030919, 0.00036456, 2.835e-05, 2.406e-05, 0.00021137, 1.332e-05, 8.712e-05]\",0.00050568,P2SH,sample_layering_network\n307711064,2015-07-21 05:30:43,\"[\"\"1R7RopEKg2tKkg3FGk2sAZXGbfGNC\"\"]\",\"[\"\"1iZvARqEVQtFF1pT5xWUq1zXUQ2gf\"\", \"\"1sSdbUCf9sJprYxco4s97HEpQuhBJ9\"\", \"\"1XDK3Gp5SbjrGta91L5PAcKqV2TUgx\"\", \"\"1QY3ekLKVvtyLe6H96apPWPW5MG4Zg3eMH\"\"]\",[0.00341259],\"[0.00069211, 0.00094867, 4.512e-05, 0.0016459]\",8.079e-05,P2PKH,sample_layering_network\n249806225,2015-07-21 05:30:43,\"[\"\"1iZvARqEVQtFF1pT5xWUq1zXUQ2gf\"\"]\",\"[\"\"1bzTjpdw2kAh6Gyo7LG2Yz42N9Y\"\", \"\"1ZcS9ajAawTNxNBApBbKQWPCQpdjtHuN\"\", \"\"1bM3HGYXp9HDtcmbJ37qGhtnSwuxPh\"\", \"\"1uE56ZHC8W6h7NaydUbs8gxiMqwSd3Zgz\"\", \"\"1kE2yxiXG9XPvTGUi4ioEmDjXQdy\"\", \"\"1o286bvMKtHpi8t4wpfdop7F5Uju2ke8\"\", \"\"1t9x5Abj4gAa45KtKTi3uVkdtqvwMr\"\"]\",[0.00069211],\"[0.00017581, 0.00011316, 6.668e-05, 4.84e-06, 8.536e-05, 0.00012147, 1.134e-05]\",0.00011345,P2SH,sample_layering_network\n158683855,2015-07-21 05:30:43,\"[\"\"1sSdbUCf9sJprYxco4s97HEpQuhBJ9\"\"]\",\"[\"\"1PrADATZTzHsTAb8JsDsRFL18vMxp\"\", \"\"1Y7hMouqzU5b64B3UcB7fyGmYXhv1\"\", \"\"15Rnqo8bzfy9y8gRkReQsby9tMa\"\", \"\"1gy5rDf74Ps7KY6DGKdxq7Hs4JtvYaqn\"\", \"\"1ddRKshdEQ1SLsbdQaDg5jTUa93SdBsNY\"\"]\",[0.00094867],\"[5.48e-06, 0.00010727, 5.683e-05, 7.472e-05, 0.00036639]\",0.00033798,P2PKH,sample_layering_network\n424404127,2015-07-21 05:30:43,\"[\"\"1QY3ekLKVvtyLe6H96apPWPW5MG4Zg3eMH\"\"]\",\"[\"\"1XwZUD7L3X9iFoaspMJDLGQPLrVrpH\"\", \"\"1LVQoXyeokG1w73vqmEcw8odLzQEQv\"\", \"\"1KXKJqVfd3eTgxFHvQ5FKDtmDV3gfkYMe\"\", \"\"16tq38FQZLSsxYpzA146bYkq6yMJKaJ\"\"]\",[0.0016459],\"[0.00033198, 0.00026649, 5.915e-05, 0.0004041]\",0.00058418,P2PKH,sample_layering_network\n364096074,2015-07-21 05:30:43,\"[\"\"1j7ohHZWkvJ2i6CDdPipXtDqT5EjB3ZWkQ\"\"]\",\"[\"\"1kthJL6kzGjDvNCrVbarNobZ5FWcz\"\", \"\"1c6fFihy1XzALhoUhiUbrRV7fZoAEQgMy\"\", \"\"1C8VWpMAXy5SbZSBL7CpWeTD4rDsRr3tX\"\", \"\"1Zg9sTC3d5KLsRfCUV14vGGK6wTbVgsV\"\", \"\"1zMVxpw8Q3fHu3YoJH77sbSg1T2\"\"]\",[0.0045437],\"[0.0001327, 0.00180945, 0.0008846, 0.00094088, 0.00014273]\",0.00063334,P2PKH,sample_layering_network\n989177655,2017-10-24 13:04:23,\"[\"\"1uconvgPjyaRcYXmHAHEVnTj4Uxw75wYC\"\"]\",\"[\"\"1DtrCgUg2oJ5WanF8e3uvBVbiQRV\"\"]\",[0.12836483],[0.12816501],0.00019982,P2PKH,sample_peeling_chain\n393037980,2017-10-24 13:04:23,\"[\"\"1DtrCgUg2oJ5WanF8e3uvBVbiQRV\"\"]\",\"[\"\"1PedQicAv7FYp4xF3WyoV28yRSQ\"\"]\",[0.12816501],[0.12813711],2.79e-05,P2PKH,sample_peeling_chain\n164236146,2017-10-24 13:04:23,\"[\"\"1PedQicAv7FYp4xF3WyoV28yRSQ\"\"]\",\"[\"\"1RRhUgzfU5Dnxayp62RrogjrVVmcC\"\"]\",[0.12813711],[0.12787531],0.0002618,P2SH,sample_peeling_chain\n686859621,2017-10-24 13:04:23,\"[\"\"1RRhUgzfU5Dnxayp62RrogjrVVmcC\"\"]\",\"[\"\"1VkBggvBmuVVZYmWUyeMgDxw9SiyiPg\"\"]\",[0.12787531],[0.12781152],6.379e-05,P2WSH,sample_peeling_chain\n464027657,2017-10-24 13:04:23,\"[\"\"1VkBggvBmuVVZYmWUyeMgDxw9SiyiPg\"\", \"\"1xN5Hev8X6RJpFgRJ9GjNjUmRHwfxikiG\"\", \"\"1Dd372XmVmWm5AtCGLJ83wz8EJEipE\"\", \"\"181NeDgY3f2AQYrfNnJMrAL9km\"\"]\",\"[\"\"1Df5PStBJgjfYdtZktwZVD47wrvVt1qwN\"\"]\",\"[0.12781152, 0.01775432, 0.01564023, 0.01915725]\",[0.17958525],0.00077807,P2PKH,sample_peeling_chain\n476803603,2017-10-24 13:04:23,\"[\"\"1Df5PStBJgjfYdtZktwZVD47wrvVt1qwN\"\"]\",\"[\"\"1kLZ4E2rdq3yPEeAV2ni3UT5enbbw\"\", \"\"194RJurRWxpzg6LujtqL9XBCRR\"\", \"\"1YY46Han1cRJX1rpBxPERDHj2EW6oc\"\", \"\"17QhLU8zWNTKSmnkfFW8ovBe5MC3gp\"\", \"\"11fi9vyYZA26Gz7cwdJi39DWPdMc8XJ\"\"]\",[0.17958525],\"[0.08494431, 0.00230385, 0.03374925, 0.02505182, 0.0328279]\",0.00070812,P2SH,sample_peeling_chain\n958039228,2017-10-24 13:04:23,\"[\"\"1kLZ4E2rdq3yPEeAV2ni3UT5enbbw\"\"]\",\"[\"\"12RYau2CUVNEgpdVVMwTqEufuU9f6\"\"]\",[0.08494431],[0.08468626],0.00025805,P2WPKH,sample_peeling_chain\n515075959,2017-10-24 13:04:23,\"[\"\"194RJurRWxpzg6LujtqL9XBCRR\"\"]\",\"[\"\"1TkjA6JKsCPc7YJnxzjBxQVFyiTYbWE\"\"]\",[0.00230385],[0.00176214],0.00054171,P2PKH,sample_peeling_chain\n114084653,2017-10-24 13:04:23,\"[\"\"1YY46Han1cRJX1rpBxPERDHj2EW6oc\"\"]\",\"[\"\"1qVEmQ6oH1VqZsqnemj4BcwMrVzwX\"\"]\",[0.03374925],[0.0330019],0.00074735,P2WPKH,sample_peeling_chain\n321685348,2017-10-24 13:04:23,\"[\"\"17QhLU8zWNTKSmnkfFW8ovBe5MC3gp\"\"]\",\"[\"\"1PU6oNmKZEJvwvTjDSxosrTThvH\"\"]\",[0.02505182],[0.02471234],0.00033948,P2WPKH,sample_peeling_chain\n443634152,2016-02-16 00:31:20,\"[\"\"1eCVWeKzN2YPemBMsTkGuenZFD\"\", \"\"1y8CCV3YcpcDmSEvYQSiJuw7vNqpWr7Vj\"\", \"\"1s6QCHWKQqdUhXBW2ivQ3RtUBu\"\"]\",\"[\"\"1TgE3Ck28iPqaaG9pHC2qcKpXTVNpG\"\", \"\"1WgBt4NNZEkW4gLb4LMNDpwm3Tnbdazq2\"\", \"\"1EGhGKfFS87aVYQmYdmA5i3oYm6\"\", \"\"1AGSrd5fFCzJW45ykwV4x2r71n9b3r9\"\", \"\"1A98jWye3Fr12PcDmpaoa9FVrg\"\"]\",\"[0.01618136, 0.00324648, 0.00314544]\",\"[5.687e-05, 0.00662575, 0.00984504, 0.0028408, 0.00261682]\",0.000588,P2WPKH,sample_mixing_pool\n514489633,2016-02-16 00:31:20,\"[\"\"1WgBt4NNZEkW4gLb4LMNDpwm3Tnbdazq2\"\", \"\"1EGhGKfFS87aVYQmYdmA5i3oYm6\"\", \"\"1AGSrd5fFCzJW45ykwV4x2r71n9b3r9\"\", \"\"1A98jWye3Fr12PcDmpaoa9FVrg\"\", \"\"1ErbZbCFVK5uN4t8oLZhvZ2zUZ1D\"\", \"\"1DJHCdGWvr88FHAc3MiBY2KYn6p6\"\"]\",\"[\"\"1CgtCj7uMWnQ3c1n7v6jLEadPiieRnnw\"\", \"\"1DwX2ZeDNgwJ5bPyfYBsd1hNSJGf\"\", \"\"1RL75ERxJ73suPSBemkqPFahKs\"\", \"\"1EyT9hAnqCsrkP7gEVKWFEwq9Zt6Mn\"\"]\",\"[0.00662575, 0.00984504, 0.0028408, 0.00261682, 1e-06, 0.0018914]\",\"[0.0109137, 0.00115947, 0.00473495, 0.00643941]\",0.00057328,P2PKH,sample_mixing_pool\n749830549,2016-02-16 00:31:20,\"[\"\"1CgtCj7uMWnQ3c1n7v6jLEadPiieRnnw\"\"]\",\"[\"\"1PY7EcS6VjqZgrG6KKpxoEpknMN6PCb\"\"]\",[0.0109137],[0.01053069],0.00038301,P2PKH,sample_mixing_pool\n270229489,2016-02-16 00:31:20,\"[\"\"1DwX2ZeDNgwJ5bPyfYBsd1hNSJGf\"\"]\",\"[\"\"1h1yonzrpdwv8XpjcMx7jvb59EFRiFc\"\"]\",[0.00115947],[0.00093946],0.00022001,P2PKH,sample_mixing_pool\n638562409,2016-02-16 00:31:20,\"[\"\"1RL75ERxJ73suPSBemkqPFahKs\"\"]\",\"[\"\"1wyiUt6wcsshHVcu64gR8gaVgc7\"\"]\",[0.00473495],[0.00467983],5.512e-05,P2WPKH,sample_mixing_pool\n408502301,2016-02-16 00:31:20,\"[\"\"1EyT9hAnqCsrkP7gEVKWFEwq9Zt6Mn\"\", \"\"1PY7EcS6VjqZgrG6KKpxoEpknMN6PCb\"\", \"\"1h1yonzrpdwv8XpjcMx7jvb59EFRiFc\"\", \"\"1wyiUt6wcsshHVcu64gR8gaVgc7\"\"]\",\"[\"\"1PKfY3x2UNrn7ZpssySpPipB3K\"\"]\",\"[0.00643941, 0.01053069, 0.00093946, 0.00467983]\",[0.02218771],0.00040168,P2SH,sample_mixing_pool\n675923571,2016-02-16 00:31:20,\"[\"\"1PKfY3x2UNrn7ZpssySpPipB3K\"\", \"\"1mCN4rn5MKA26vsZ4AaQvbNgvdvk\"\", \"\"18sf6gxaqBNvYHKNLAtLHqabpKBz\"\", \"\"1WwN3QaPvtafmmyGMQpMeGnmH5i\"\", \"\"1hXRHUR5jFgj8NBtVkSA8Tr56ZsUsj\"\"]\",\"[\"\"1T47NasMig8BFdAjs6TSGeuwp2S\"\", \"\"1iJxXv3xeubZ5eoYFW2MZjw8iu\"\", \"\"1p6txDUe3LiR5utEEJVZWUyQnNQDEjvApu\"\", \"\"1vmByySupg2mZ1vEcu1i7B4h46ro\"\", \"\"1fYqQHb7AhqgUwBvFHEEyZR7BnTxgAj\"\"]\",\"[0.02218771, 0.0015647, 0.00149486, 0.00010278, 0.00134432]\",\"[0.00076007, 0.01285369, 0.00471702, 0.00465558, 0.003308]\",0.00040001,P2SH,sample_mixing_pool\n367847692,2016-02-16 00:31:20,\"[\"\"1iJxXv3xeubZ5eoYFW2MZjw8iu\"\", \"\"1p6txDUe3LiR5utEEJVZWUyQnNQDEjvApu\"\", \"\"1vmByySupg2mZ1vEcu1i7B4h46ro\"\", \"\"1fYqQHb7AhqgUwBvFHEEyZR7BnTxgAj\"\", \"\"1bbvFvE4ZZA4TKoeKundNooybv\"\", \"\"1mM2SuQeiBVMZJZCxPBdKY8GuM\"\", \"\"1bTsuNobydAH9A2PCyCU5GwbuJ4\"\", \"\"1vAGZ9tmRSEhwD527p1BiyNr6Gxcz5xo93\"\"]\",\"[\"\"1Px6fuKhnnw6e4tytg2yHJEMo8MyJ6Uw\"\"]\",\"[0.01285369, 0.00471702, 0.00465558, 0.003308, 0.00195956, 0.00250751, 0.00132968, 0.001375]\",[0.03234593],0.00036011,P2WPKH,sample_mixing_pool\n611959180,2016-02-16 00:31:20,\"[\"\"1Px6fuKhnnw6e4tytg2yHJEMo8MyJ6Uw\"\"]\",\"[\"\"1H6Dj5ZmNzDhPCHNm2ZMQgRSwYj\"\"]\",[0.03234593],[0.0317642],0.00058173,P2WPKH,sample_mixing_pool\n698602804,2016-02-16 00:31:20,\"[\"\"1H6Dj5ZmNzDhPCHNm2ZMQgRSwYj\"\"]\",\"[\"\"1eydxjs41Pfc16MJtJjkdyxtNTnu\"\"]\",[0.0317642],[0.03139376],0.00037044,P2WPKH,sample_mixing_pool\n240783740,2016-02-16 00:31:20,\"[\"\"1eydxjs41Pfc16MJtJjkdyxtNTnu\"\"]\",\"[\"\"1P3eF4baAGBXWAT8hfWGxv2HEnnp\"\"]\",[0.03139376],[0.03096381],0.00042995,P2SH,sample_mixing_pool\n397085130,2016-02-16 00:31:20,\"[\"\"1P3eF4baAGBXWAT8hfWGxv2HEnnp\"\"]\",\"[\"\"1NYsLJCca7R9UNHXv37EUJs4uX\"\"]\",[0.03096381],[0.03045258],0.00051123,P2WPKH,sample_mixing_pool\n246386685,2016-02-16 00:31:20,\"[\"\"1NYsLJCca7R9UNHXv37EUJs4uX\"\"]\",\"[\"\"1UPJanW8fxKLUC9Zrv5H2KwBbUL6k\"\"]\",[0.03045258],[0.02965887],0.00079371,P2WPKH,sample_mixing_pool\n502037224,2016-02-16 00:31:20,\"[\"\"1UPJanW8fxKLUC9Zrv5H2KwBbUL6k\"\"]\",\"[\"\"1cYmzv6RXENcngYP5Z1uM88VNevjotuqgy\"\"]\",[0.02965887],[0.02887272],0.00078615,P2WPKH,sample_mixing_pool\n422053777,2016-02-16 00:31:20,\"[\"\"1cYmzv6RXENcngYP5Z1uM88VNevjotuqgy\"\", \"\"1kJ6PYVdCtSFFkpDynkLMCeJBGpzv2h\"\", \"\"1KQRgs93YhA4Sx34kGMWBFwo9kBfm\"\", \"\"1vT3Zndwyi76mf5aZoM7cLGfFJcJsytNxx\"\"]\",\"[\"\"1gFbByw6EzNcj8Y4EbMf8sJ342eZMF8\"\", \"\"1NhE7rsQ4m2ueqGfioRpuGhTa2fhoMD\"\", \"\"1bBGARBKmwTwD8xikWPTTiAebFMcruo\"\", \"\"16C3tzrtej72GKPvCoDi2VXVE451jqAPob\"\", \"\"1no9KgohNfDPsxvk1nHPy1ycThsa4fgbjm\"\", \"\"1QEhYTxNpryaLUD1nBhL1qA8s79g\"\"]\",\"[0.02887272, 0.00281159, 0.00127368, 0.00260571]\",\"[0.0122865, 0.00179391, 0.00238791, 0.01180913, 0.00114696, 0.00539737]\",0.00074192,P2WSH,sample_mixing_pool\n430894294,2015-10-16 05:47:25,\"[\"\"1bs5iPLdFjEHkWzFAPTtMZmWAHF\"\"]\",\"[\"\"1GtTjrBX92L5RL4QjKmoeuNbs9cBEYcd\"\"]\",[1572.10555491],[1572.10528742],0.00026749,P2WPKH,sample_licit_commerce\n511495908,2015-10-16 05:47:25,\"[\"\"1GtTjrBX92L5RL4QjKmoeuNbs9cBEYcd\"\"]\",\"[\"\"1xB8Dj2FBAXbRT7eQH5nSgtKME1UWusEv\"\", \"\"1UMVbFq2Pxw5qYchFs7XYTux5pdY\"\", \"\"1VibkBxo6dxSbu8JtUWMvG1GPE\"\", \"\"1xT9NrChtpqwQdEwVU4cRBF3TK8wqVef\"\"]\",[1572.10528742],\"[322.95552869, 873.1272622, 339.92347716, 36.09822617]\",0.0007932,P2SH,sample_licit_commerce\n591937218,2015-10-16 05:47:25,\"[\"\"1xB8Dj2FBAXbRT7eQH5nSgtKME1UWusEv\"\"]\",\"[\"\"1y8R7VY5P132SweHXBVa2GXaZrZqaH\"\"]\",[322.95552869],[322.95499532],0.00053337,P2PKH,sample_licit_commerce\n505199065,2015-10-16 05:47:25,\"[\"\"1UMVbFq2Pxw5qYchFs7XYTux5pdY\"\"]\",\"[\"\"1yTSCa9dPpXBbjfcijpBYxAdvAU8RV\"\", \"\"1HKVPRRXEkoN6RzVbkJp6kjS68Yj3xgAb\"\", \"\"1C7qHcuqnGb6Qiz6rsG73EjW3pPh\"\"]\",[873.1272622],\"[110.65228661, 523.80153197, 238.67267037]\",0.00077325,P2PKH,sample_licit_commerce\n282026767,2015-10-16 05:47:25,\"[\"\"1VibkBxo6dxSbu8JtUWMvG1GPE\"\"]\",\"[\"\"1Rwkabd3FWPY3oPXF7EcJYA83iET\"\", \"\"1L8RfHSkdvtbVtRvBcYttqkvSLLX\"\", \"\"1EB3fw14YHPkHtVfs7kbsc1jgM6WLhG\"\", \"\"1NhucNu22XYNgT3QPGkf7wbrqo9wnDw3Vj\"\", \"\"1ufCP4SGyWWfUGrN2mz1UCE7Uwz1GQ7vQx\"\", \"\"1BgEcdu1FyhUYaJwXSv8fAVkJauZQb2z\"\", \"\"1gnaezUF6EbpTpARNt2dBcAKmPY\"\"]\",[339.92347716],\"[15.73531123, 110.75560664, 17.41998495, 18.15967671, 75.14136022, 34.42161368, 68.28951686]\",0.00040687,P2SH,sample_licit_commerce";

const SAMPLE_NETWORK_CSV = "txid,relay_timestamp,relay_ip,relay_port,node_type,country_code,asn,isp,protocol_version,user_agent\n156686565,2016-08-07 14:26:10.912,123.23.218.20,8333,bulletproof_host,GB,AS2856,British Telecommunications,70015,/Satoshi:22.0.0/\n506784234,2016-08-07 14:26:10.732,142.60.216.4,8333,mobile,FR,AS16276,OVH SAS,70015,/Satoshi:21.1.0/\n758883601,2016-08-07 14:26:10.822,123.23.218.20,8333,residential,GB,AS2856,British Telecommunications,70015,/Satoshi:22.0.0/\n179262906,2015-07-21 05:30:42.692,144.226.24.65,8333,mobile,IN,AS55836,Reliance Jio Infocomm,70015,/Satoshi:21.1.0/\n629099363,2015-07-21 05:30:42.629,144.226.24.65,8333,vpn_proxy,IN,AS55836,Reliance Jio Infocomm,70015,/Satoshi:22.0.0/\n683433672,2015-07-21 05:30:42.680,144.226.24.65,8333,datacenter,CA,AS812,Rogers Communications,70015,/btcd:0.22.0/\n307711064,2015-07-21 05:30:42.789,144.226.24.65,64832,vpn_proxy,CA,AS812,Rogers Communications,70015,/Satoshi:0.20.1/\n249806225,2015-07-21 05:30:42.907,144.226.24.65,8333,residential,IN,AS55836,Reliance Jio Infocomm,70015,/Satoshi:22.0.0/\n158683855,2015-07-21 05:30:42.869,163.33.35.150,8333,vpn_proxy,IN,AS55836,Reliance Jio Infocomm,70015,/Satoshi:22.0.0/\n424404127,2015-07-21 05:30:42.938,163.33.35.150,56768,residential,CA,AS812,Rogers Communications,70015,/Satoshi:21.1.0/\n364096074,2015-07-21 05:30:42.895,144.226.24.65,8333,mobile,IN,AS55836,Reliance Jio Infocomm,70015,/Satoshi:0.20.1/\n989177655,2017-10-24 13:04:22.540,123.183.121.110,8333,residential,DE,AS3320,Deutsche Telekom AG,70015,/Satoshi:0.20.1/\n393037980,2017-10-24 13:04:22.573,123.183.121.110,8333,bulletproof_host,DE,AS3320,Deutsche Telekom AG,70015,/Satoshi:22.0.0/\n164236146,2017-10-24 13:04:22.934,123.183.121.110,59072,residential,DE,AS3320,Deutsche Telekom AG,70015,/Satoshi:21.1.0/\n686859621,2017-10-24 13:04:22.896,142.220.105.93,8333,residential,BR,AS28573,Claro Brasil,70015,/Satoshi:22.0.0/\n464027657,2017-10-24 13:04:22.541,123.183.121.110,8333,residential,DE,AS3320,Deutsche Telekom AG,70015,/Satoshi:22.0.0/\n476803603,2017-10-24 13:04:22.674,123.183.121.110,8333,vpn_proxy,BR,AS28573,Claro Brasil,70015,/Satoshi:22.0.0/\n958039228,2017-10-24 13:04:22.836,123.183.121.110,53440,residential,DE,AS3320,Deutsche Telekom AG,70015,/Satoshi:21.1.0/\n515075959,2017-10-24 13:04:22.619,142.220.105.93,8333,tor_exit_node,DE,AS3320,Deutsche Telekom AG,70015,/Satoshi:22.0.0/\n114084653,2017-10-24 13:04:22.711,123.183.121.110,60864,datacenter,BR,AS28573,Claro Brasil,70015,/Satoshi:0.20.1/\n321685348,2017-10-24 13:04:22.899,142.220.105.93,8333,residential,DE,AS3320,Deutsche Telekom AG,70015,/Satoshi:22.0.0/\n443634152,2016-02-16 00:31:19.742,129.221.245.94,8333,vpn_proxy,BZ,AS49870,Alentus Corp (Proxy Gateway),70015,/Satoshi:22.0.0/\n514489633,2016-02-16 00:31:19.893,129.221.245.94,8333,bulletproof_host,BZ,AS49870,Alentus Corp (Proxy Gateway),70015,/Satoshi:22.0.0/\n749830549,2016-02-16 00:31:19.821,129.221.245.94,58432,bulletproof_host,BZ,AS49870,Alentus Corp (Proxy Gateway),70015,/Satoshi:0.20.1/\n270229489,2016-02-16 00:31:19.764,129.221.245.94,8333,residential,BZ,AS49870,Alentus Corp (Proxy Gateway),70015,/Satoshi:22.0.0/\n638562409,2016-02-16 00:31:19.790,129.221.245.94,8333,tor_exit_node,BZ,AS49870,Alentus Corp (Proxy Gateway),70015,/Satoshi:22.0.0/\n408502301,2016-02-16 00:31:19.845,129.221.245.94,50496,datacenter,BZ,AS49870,Alentus Corp (Proxy Gateway),70015,/Satoshi:22.0.0/\n675923571,2016-02-16 00:31:19.543,129.221.245.94,8333,tor_exit_node,BZ,AS49870,Alentus Corp (Proxy Gateway),70015,/Satoshi:22.0.0/\n367847692,2016-02-16 00:31:19.657,129.221.245.94,18333,residential,BZ,AS49870,Alentus Corp (Proxy Gateway),70015,/Satoshi:22.0.0/\n611959180,2016-02-16 00:31:19.679,129.221.245.94,8333,mobile,BZ,AS49870,Alentus Corp (Proxy Gateway),70015,/Satoshi:22.0.0/\n698602804,2016-02-16 00:31:19.675,129.221.245.94,8333,bulletproof_host,BZ,AS49870,Alentus Corp (Proxy Gateway),70015,/Satoshi:0.20.1/\n240783740,2016-02-16 00:31:19.801,129.221.245.94,8333,bulletproof_host,BZ,AS49870,Alentus Corp (Proxy Gateway),70015,/Satoshi:22.0.0/\n397085130,2016-02-16 00:31:19.888,129.221.245.94,8333,residential,BZ,AS49870,Alentus Corp (Proxy Gateway),70015,/Satoshi:0.20.1/\n246386685,2016-02-16 00:31:19.606,129.221.245.94,50624,bulletproof_host,BZ,AS49870,Alentus Corp (Proxy Gateway),70015,/Satoshi:22.0.0/\n502037224,2016-02-16 00:31:19.801,129.221.245.94,8333,mobile,BZ,AS49870,Alentus Corp (Proxy Gateway),70015,/Satoshi:22.0.0/\n422053777,2016-02-16 00:31:19.564,129.221.245.94,8333,datacenter,BZ,AS49870,Alentus Corp (Proxy Gateway),70015,/Satoshi:22.0.0/\n430894294,2015-10-16 05:47:24.886,120.144.43.62,59008,datacenter,RU,AS210644,AEZA International LTD,70015,/Satoshi:0.20.1/\n511495908,2015-10-16 05:47:24.681,120.144.43.62,8333,mobile,RU,AS210644,AEZA International LTD,70015,/Satoshi:0.20.1/\n591937218,2015-10-16 05:47:24.818,120.144.43.62,8333,mobile,GB,AS2856,British Telecommunications,70015,/Satoshi:21.1.0/\n505199065,2015-10-16 05:47:24.713,139.181.156.109,8333,tor_exit_node,RU,AS210644,AEZA International LTD,70015,/Satoshi:22.0.0/\n282026767,2015-10-16 05:47:24.813,120.144.43.62,8333,residential,RU,AS210644,AEZA International LTD,70015,/btcd:0.22.0/";

const SAMPLE_SINGLE_BATCH_CSV = "txid,timestamp,input_addresses,output_addresses,input_amounts,output_amounts,fee_btc,script_type,scenario_id,relay_timestamp,relay_ip,relay_port,node_type,country_code,asn,isp,protocol_version,user_agent\n156686565,2016-08-07 14:26:11,\"[\"\"1Awg2jyQSht5DXTnMB5d53wgW7RAEamG\"\", \"\"1tNRGVoahTgCe96jiEeKTmmbbp89z\"\"]\",\"[\"\"1h5QvPBsQVeYheDV6BwF3W7DL2vBX\"\"]\",\"[0.01688925, 0.00175668]\",[0.01822274],0.00042319,P2WPKH,sample_ransomware_campaign,2016-08-07 14:26:10.912,123.23.218.20,8333,bulletproof_host,GB,AS2856,British Telecommunications,70015,/Satoshi:22.0.0/\n506784234,2016-08-07 14:26:11,\"[\"\"1h5QvPBsQVeYheDV6BwF3W7DL2vBX\"\"]\",\"[\"\"1ZdMGsxaDPnGUZPvCH8sWj5ZYcs66w\"\"]\",[0.01822274],[0.01798583],0.00023691,P2PKH,sample_ransomware_campaign,2016-08-07 14:26:10.732,142.60.216.4,8333,mobile,FR,AS16276,OVH SAS,70015,/Satoshi:21.1.0/\n758883601,2016-08-07 14:26:11,\"[\"\"1ZdMGsxaDPnGUZPvCH8sWj5ZYcs66w\"\"]\",\"[\"\"159AMGmaAsa6RFuNj7iMN9ntJPhTip45k6\"\"]\",[0.01798583],[0.01794007],4.576e-05,P2PKH,sample_ransomware_campaign,2016-08-07 14:26:10.822,123.23.218.20,8333,residential,GB,AS2856,British Telecommunications,70015,/Satoshi:22.0.0/\n179262906,2015-07-21 05:30:43,\"[\"\"1CXFBDpTuaLQXX8rENriUC8zJfd8mGC\"\"]\",\"[\"\"1oaRZpfiSTKMorEiPCv6mWNse25gL\"\", \"\"1B5B9EjL9u2CAx5DALAYKKqArBRje\"\", \"\"1R7RopEKg2tKkg3FGk2sAZXGbfGNC\"\"]\",[0.00647458],\"[0.00112425, 0.00154365, 0.00341259]\",0.00039409,P2WPKH,sample_layering_network,2015-07-21 05:30:42.692,144.226.24.65,8333,mobile,IN,AS55836,Reliance Jio Infocomm,70015,/Satoshi:21.1.0/\n629099363,2015-07-21 05:30:43,\"[\"\"1oaRZpfiSTKMorEiPCv6mWNse25gL\"\"]\",\"[\"\"17gpHuZqA9gf9QEaj6jhvgLpBZQ\"\", \"\"1Q1ifdAeRzUU1wvLeofhYSJ4frkKW\"\", \"\"1PbbWdKLeHEkvLtKF8f9BKnVeciZLWxGV\"\", \"\"1fN91WxySVZ1Zj51CXScB9dg7suaPyJ\"\", \"\"1mfTT7iHfoQmCCHx1mm4xGx3hMTU238Uj\"\"]\",[0.00112425],\"[0.00017906, 7.406e-05, 1.201e-05, 0.00018174, 0.00024584]\",0.00043154,P2WSH,sample_layering_network,2015-07-21 05:30:42.629,144.226.24.65,8333,vpn_proxy,IN,AS55836,Reliance Jio Infocomm,70015,/Satoshi:22.0.0/\n683433672,2015-07-21 05:30:43,\"[\"\"1B5B9EjL9u2CAx5DALAYKKqArBRje\"\"]\",\"[\"\"1ZbosnydtedJ9yG1Y7rbutXwhVW\"\", \"\"1uwUZsfGNsnQqEpC7PAnUDgTKP\"\", \"\"1Fw9gLtg4GtkQ4ZwXjBQ6uFsUfK6LxX\"\", \"\"1hjGtk5KGzEhnfJEMYg8dVzAZtPYwr\"\", \"\"1LXPLTCWKtRnA94V3kgRD6QY23uZL8igwu\"\", \"\"1uzq8nBm1e5dxsArYSYiq9Hky3dDwcFQ\"\", \"\"1afGPa5zW7kEG8G2okaXVtYzX5X\"\"]\",[0.00154365],\"[0.00030919, 0.00036456, 2.835e-05, 2.406e-05, 0.00021137, 1.332e-05, 8.712e-05]\",0.00050568,P2SH,sample_layering_network,2015-07-21 05:30:42.680,144.226.24.65,8333,datacenter,CA,AS812,Rogers Communications,70015,/btcd:0.22.0/\n307711064,2015-07-21 05:30:43,\"[\"\"1R7RopEKg2tKkg3FGk2sAZXGbfGNC\"\"]\",\"[\"\"1iZvARqEVQtFF1pT5xWUq1zXUQ2gf\"\", \"\"1sSdbUCf9sJprYxco4s97HEpQuhBJ9\"\", \"\"1XDK3Gp5SbjrGta91L5PAcKqV2TUgx\"\", \"\"1QY3ekLKVvtyLe6H96apPWPW5MG4Zg3eMH\"\"]\",[0.00341259],\"[0.00069211, 0.00094867, 4.512e-05, 0.0016459]\",8.079e-05,P2PKH,sample_layering_network,2015-07-21 05:30:42.789,144.226.24.65,64832,vpn_proxy,CA,AS812,Rogers Communications,70015,/Satoshi:0.20.1/\n249806225,2015-07-21 05:30:43,\"[\"\"1iZvARqEVQtFF1pT5xWUq1zXUQ2gf\"\"]\",\"[\"\"1bzTjpdw2kAh6Gyo7LG2Yz42N9Y\"\", \"\"1ZcS9ajAawTNxNBApBbKQWPCQpdjtHuN\"\", \"\"1bM3HGYXp9HDtcmbJ37qGhtnSwuxPh\"\", \"\"1uE56ZHC8W6h7NaydUbs8gxiMqwSd3Zgz\"\", \"\"1kE2yxiXG9XPvTGUi4ioEmDjXQdy\"\", \"\"1o286bvMKtHpi8t4wpfdop7F5Uju2ke8\"\", \"\"1t9x5Abj4gAa45KtKTi3uVkdtqvwMr\"\"]\",[0.00069211],\"[0.00017581, 0.00011316, 6.668e-05, 4.84e-06, 8.536e-05, 0.00012147, 1.134e-05]\",0.00011345,P2SH,sample_layering_network,2015-07-21 05:30:42.907,144.226.24.65,8333,residential,IN,AS55836,Reliance Jio Infocomm,70015,/Satoshi:22.0.0/\n158683855,2015-07-21 05:30:43,\"[\"\"1sSdbUCf9sJprYxco4s97HEpQuhBJ9\"\"]\",\"[\"\"1PrADATZTzHsTAb8JsDsRFL18vMxp\"\", \"\"1Y7hMouqzU5b64B3UcB7fyGmYXhv1\"\", \"\"15Rnqo8bzfy9y8gRkReQsby9tMa\"\", \"\"1gy5rDf74Ps7KY6DGKdxq7Hs4JtvYaqn\"\", \"\"1ddRKshdEQ1SLsbdQaDg5jTUa93SdBsNY\"\"]\",[0.00094867],\"[5.48e-06, 0.00010727, 5.683e-05, 7.472e-05, 0.00036639]\",0.00033798,P2PKH,sample_layering_network,2015-07-21 05:30:42.869,163.33.35.150,8333,vpn_proxy,IN,AS55836,Reliance Jio Infocomm,70015,/Satoshi:22.0.0/\n424404127,2015-07-21 05:30:43,\"[\"\"1QY3ekLKVvtyLe6H96apPWPW5MG4Zg3eMH\"\"]\",\"[\"\"1XwZUD7L3X9iFoaspMJDLGQPLrVrpH\"\", \"\"1LVQoXyeokG1w73vqmEcw8odLzQEQv\"\", \"\"1KXKJqVfd3eTgxFHvQ5FKDtmDV3gfkYMe\"\", \"\"16tq38FQZLSsxYpzA146bYkq6yMJKaJ\"\"]\",[0.0016459],\"[0.00033198, 0.00026649, 5.915e-05, 0.0004041]\",0.00058418,P2PKH,sample_layering_network,2015-07-21 05:30:42.938,163.33.35.150,56768,residential,CA,AS812,Rogers Communications,70015,/Satoshi:21.1.0/\n364096074,2015-07-21 05:30:43,\"[\"\"1j7ohHZWkvJ2i6CDdPipXtDqT5EjB3ZWkQ\"\"]\",\"[\"\"1kthJL6kzGjDvNCrVbarNobZ5FWcz\"\", \"\"1c6fFihy1XzALhoUhiUbrRV7fZoAEQgMy\"\", \"\"1C8VWpMAXy5SbZSBL7CpWeTD4rDsRr3tX\"\", \"\"1Zg9sTC3d5KLsRfCUV14vGGK6wTbVgsV\"\", \"\"1zMVxpw8Q3fHu3YoJH77sbSg1T2\"\"]\",[0.0045437],\"[0.0001327, 0.00180945, 0.0008846, 0.00094088, 0.00014273]\",0.00063334,P2PKH,sample_layering_network,2015-07-21 05:30:42.895,144.226.24.65,8333,mobile,IN,AS55836,Reliance Jio Infocomm,70015,/Satoshi:0.20.1/\n989177655,2017-10-24 13:04:23,\"[\"\"1uconvgPjyaRcYXmHAHEVnTj4Uxw75wYC\"\"]\",\"[\"\"1DtrCgUg2oJ5WanF8e3uvBVbiQRV\"\"]\",[0.12836483],[0.12816501],0.00019982,P2PKH,sample_peeling_chain,2017-10-24 13:04:22.540,123.183.121.110,8333,residential,DE,AS3320,Deutsche Telekom AG,70015,/Satoshi:0.20.1/\n393037980,2017-10-24 13:04:23,\"[\"\"1DtrCgUg2oJ5WanF8e3uvBVbiQRV\"\"]\",\"[\"\"1PedQicAv7FYp4xF3WyoV28yRSQ\"\"]\",[0.12816501],[0.12813711],2.79e-05,P2PKH,sample_peeling_chain,2017-10-24 13:04:22.573,123.183.121.110,8333,bulletproof_host,DE,AS3320,Deutsche Telekom AG,70015,/Satoshi:22.0.0/\n164236146,2017-10-24 13:04:23,\"[\"\"1PedQicAv7FYp4xF3WyoV28yRSQ\"\"]\",\"[\"\"1RRhUgzfU5Dnxayp62RrogjrVVmcC\"\"]\",[0.12813711],[0.12787531],0.0002618,P2SH,sample_peeling_chain,2017-10-24 13:04:22.934,123.183.121.110,59072,residential,DE,AS3320,Deutsche Telekom AG,70015,/Satoshi:21.1.0/\n686859621,2017-10-24 13:04:23,\"[\"\"1RRhUgzfU5Dnxayp62RrogjrVVmcC\"\"]\",\"[\"\"1VkBggvBmuVVZYmWUyeMgDxw9SiyiPg\"\"]\",[0.12787531],[0.12781152],6.379e-05,P2WSH,sample_peeling_chain,2017-10-24 13:04:22.896,142.220.105.93,8333,residential,BR,AS28573,Claro Brasil,70015,/Satoshi:22.0.0/\n464027657,2017-10-24 13:04:23,\"[\"\"1VkBggvBmuVVZYmWUyeMgDxw9SiyiPg\"\", \"\"1xN5Hev8X6RJpFgRJ9GjNjUmRHwfxikiG\"\", \"\"1Dd372XmVmWm5AtCGLJ83wz8EJEipE\"\", \"\"181NeDgY3f2AQYrfNnJMrAL9km\"\"]\",\"[\"\"1Df5PStBJgjfYdtZktwZVD47wrvVt1qwN\"\"]\",\"[0.12781152, 0.01775432, 0.01564023, 0.01915725]\",[0.17958525],0.00077807,P2PKH,sample_peeling_chain,2017-10-24 13:04:22.541,123.183.121.110,8333,residential,DE,AS3320,Deutsche Telekom AG,70015,/Satoshi:22.0.0/\n476803603,2017-10-24 13:04:23,\"[\"\"1Df5PStBJgjfYdtZktwZVD47wrvVt1qwN\"\"]\",\"[\"\"1kLZ4E2rdq3yPEeAV2ni3UT5enbbw\"\", \"\"194RJurRWxpzg6LujtqL9XBCRR\"\", \"\"1YY46Han1cRJX1rpBxPERDHj2EW6oc\"\", \"\"17QhLU8zWNTKSmnkfFW8ovBe5MC3gp\"\", \"\"11fi9vyYZA26Gz7cwdJi39DWPdMc8XJ\"\"]\",[0.17958525],\"[0.08494431, 0.00230385, 0.03374925, 0.02505182, 0.0328279]\",0.00070812,P2SH,sample_peeling_chain,2017-10-24 13:04:22.674,123.183.121.110,8333,vpn_proxy,BR,AS28573,Claro Brasil,70015,/Satoshi:22.0.0/\n958039228,2017-10-24 13:04:23,\"[\"\"1kLZ4E2rdq3yPEeAV2ni3UT5enbbw\"\"]\",\"[\"\"12RYau2CUVNEgpdVVMwTqEufuU9f6\"\"]\",[0.08494431],[0.08468626],0.00025805,P2WPKH,sample_peeling_chain,2017-10-24 13:04:22.836,123.183.121.110,53440,residential,DE,AS3320,Deutsche Telekom AG,70015,/Satoshi:21.1.0/\n515075959,2017-10-24 13:04:23,\"[\"\"194RJurRWxpzg6LujtqL9XBCRR\"\"]\",\"[\"\"1TkjA6JKsCPc7YJnxzjBxQVFyiTYbWE\"\"]\",[0.00230385],[0.00176214],0.00054171,P2PKH,sample_peeling_chain,2017-10-24 13:04:22.619,142.220.105.93,8333,tor_exit_node,DE,AS3320,Deutsche Telekom AG,70015,/Satoshi:22.0.0/\n114084653,2017-10-24 13:04:23,\"[\"\"1YY46Han1cRJX1rpBxPERDHj2EW6oc\"\"]\",\"[\"\"1qVEmQ6oH1VqZsqnemj4BcwMrVzwX\"\"]\",[0.03374925],[0.0330019],0.00074735,P2WPKH,sample_peeling_chain,2017-10-24 13:04:22.711,123.183.121.110,60864,datacenter,BR,AS28573,Claro Brasil,70015,/Satoshi:0.20.1/\n321685348,2017-10-24 13:04:23,\"[\"\"17QhLU8zWNTKSmnkfFW8ovBe5MC3gp\"\"]\",\"[\"\"1PU6oNmKZEJvwvTjDSxosrTThvH\"\"]\",[0.02505182],[0.02471234],0.00033948,P2WPKH,sample_peeling_chain,2017-10-24 13:04:22.899,142.220.105.93,8333,residential,DE,AS3320,Deutsche Telekom AG,70015,/Satoshi:22.0.0/\n443634152,2016-02-16 00:31:20,\"[\"\"1eCVWeKzN2YPemBMsTkGuenZFD\"\", \"\"1y8CCV3YcpcDmSEvYQSiJuw7vNqpWr7Vj\"\", \"\"1s6QCHWKQqdUhXBW2ivQ3RtUBu\"\"]\",\"[\"\"1TgE3Ck28iPqaaG9pHC2qcKpXTVNpG\"\", \"\"1WgBt4NNZEkW4gLb4LMNDpwm3Tnbdazq2\"\", \"\"1EGhGKfFS87aVYQmYdmA5i3oYm6\"\", \"\"1AGSrd5fFCzJW45ykwV4x2r71n9b3r9\"\", \"\"1A98jWye3Fr12PcDmpaoa9FVrg\"\"]\",\"[0.01618136, 0.00324648, 0.00314544]\",\"[5.687e-05, 0.00662575, 0.00984504, 0.0028408, 0.00261682]\",0.000588,P2WPKH,sample_mixing_pool,2016-02-16 00:31:19.742,129.221.245.94,8333,vpn_proxy,BZ,AS49870,Alentus Corp (Proxy Gateway),70015,/Satoshi:22.0.0/\n514489633,2016-02-16 00:31:20,\"[\"\"1WgBt4NNZEkW4gLb4LMNDpwm3Tnbdazq2\"\", \"\"1EGhGKfFS87aVYQmYdmA5i3oYm6\"\", \"\"1AGSrd5fFCzJW45ykwV4x2r71n9b3r9\"\", \"\"1A98jWye3Fr12PcDmpaoa9FVrg\"\", \"\"1ErbZbCFVK5uN4t8oLZhvZ2zUZ1D\"\", \"\"1DJHCdGWvr88FHAc3MiBY2KYn6p6\"\"]\",\"[\"\"1CgtCj7uMWnQ3c1n7v6jLEadPiieRnnw\"\", \"\"1DwX2ZeDNgwJ5bPyfYBsd1hNSJGf\"\", \"\"1RL75ERxJ73suPSBemkqPFahKs\"\", \"\"1EyT9hAnqCsrkP7gEVKWFEwq9Zt6Mn\"\"]\",\"[0.00662575, 0.00984504, 0.0028408, 0.00261682, 1e-06, 0.0018914]\",\"[0.0109137, 0.00115947, 0.00473495, 0.00643941]\",0.00057328,P2PKH,sample_mixing_pool,2016-02-16 00:31:19.893,129.221.245.94,8333,bulletproof_host,BZ,AS49870,Alentus Corp (Proxy Gateway),70015,/Satoshi:22.0.0/\n749830549,2016-02-16 00:31:20,\"[\"\"1CgtCj7uMWnQ3c1n7v6jLEadPiieRnnw\"\"]\",\"[\"\"1PY7EcS6VjqZgrG6KKpxoEpknMN6PCb\"\"]\",[0.0109137],[0.01053069],0.00038301,P2PKH,sample_mixing_pool,2016-02-16 00:31:19.821,129.221.245.94,58432,bulletproof_host,BZ,AS49870,Alentus Corp (Proxy Gateway),70015,/Satoshi:0.20.1/\n270229489,2016-02-16 00:31:20,\"[\"\"1DwX2ZeDNgwJ5bPyfYBsd1hNSJGf\"\"]\",\"[\"\"1h1yonzrpdwv8XpjcMx7jvb59EFRiFc\"\"]\",[0.00115947],[0.00093946],0.00022001,P2PKH,sample_mixing_pool,2016-02-16 00:31:19.764,129.221.245.94,8333,residential,BZ,AS49870,Alentus Corp (Proxy Gateway),70015,/Satoshi:22.0.0/\n638562409,2016-02-16 00:31:20,\"[\"\"1RL75ERxJ73suPSBemkqPFahKs\"\"]\",\"[\"\"1wyiUt6wcsshHVcu64gR8gaVgc7\"\"]\",[0.00473495],[0.00467983],5.512e-05,P2WPKH,sample_mixing_pool,2016-02-16 00:31:19.790,129.221.245.94,8333,tor_exit_node,BZ,AS49870,Alentus Corp (Proxy Gateway),70015,/Satoshi:22.0.0/\n408502301,2016-02-16 00:31:20,\"[\"\"1EyT9hAnqCsrkP7gEVKWFEwq9Zt6Mn\"\", \"\"1PY7EcS6VjqZgrG6KKpxoEpknMN6PCb\"\", \"\"1h1yonzrpdwv8XpjcMx7jvb59EFRiFc\"\", \"\"1wyiUt6wcsshHVcu64gR8gaVgc7\"\"]\",\"[\"\"1PKfY3x2UNrn7ZpssySpPipB3K\"\"]\",\"[0.00643941, 0.01053069, 0.00093946, 0.00467983]\",[0.02218771],0.00040168,P2SH,sample_mixing_pool,2016-02-16 00:31:19.845,129.221.245.94,50496,datacenter,BZ,AS49870,Alentus Corp (Proxy Gateway),70015,/Satoshi:22.0.0/\n675923571,2016-02-16 00:31:20,\"[\"\"1PKfY3x2UNrn7ZpssySpPipB3K\"\", \"\"1mCN4rn5MKA26vsZ4AaQvbNgvdvk\"\", \"\"18sf6gxaqBNvYHKNLAtLHqabpKBz\"\", \"\"1WwN3QaPvtafmmyGMQpMeGnmH5i\"\", \"\"1hXRHUR5jFgj8NBtVkSA8Tr56ZsUsj\"\"]\",\"[\"\"1T47NasMig8BFdAjs6TSGeuwp2S\"\", \"\"1iJxXv3xeubZ5eoYFW2MZjw8iu\"\", \"\"1p6txDUe3LiR5utEEJVZWUyQnNQDEjvApu\"\", \"\"1vmByySupg2mZ1vEcu1i7B4h46ro\"\", \"\"1fYqQHb7AhqgUwBvFHEEyZR7BnTxgAj\"\"]\",\"[0.02218771, 0.0015647, 0.00149486, 0.00010278, 0.00134432]\",\"[0.00076007, 0.01285369, 0.00471702, 0.00465558, 0.003308]\",0.00040001,P2SH,sample_mixing_pool,2016-02-16 00:31:19.543,129.221.245.94,8333,tor_exit_node,BZ,AS49870,Alentus Corp (Proxy Gateway),70015,/Satoshi:22.0.0/\n367847692,2016-02-16 00:31:20,\"[\"\"1iJxXv3xeubZ5eoYFW2MZjw8iu\"\", \"\"1p6txDUe3LiR5utEEJVZWUyQnNQDEjvApu\"\", \"\"1vmByySupg2mZ1vEcu1i7B4h46ro\"\", \"\"1fYqQHb7AhqgUwBvFHEEyZR7BnTxgAj\"\", \"\"1bbvFvE4ZZA4TKoeKundNooybv\"\", \"\"1mM2SuQeiBVMZJZCxPBdKY8GuM\"\", \"\"1bTsuNobydAH9A2PCyCU5GwbuJ4\"\", \"\"1vAGZ9tmRSEhwD527p1BiyNr6Gxcz5xo93\"\"]\",\"[\"\"1Px6fuKhnnw6e4tytg2yHJEMo8MyJ6Uw\"\"]\",\"[0.01285369, 0.00471702, 0.00465558, 0.003308, 0.00195956, 0.00250751, 0.00132968, 0.001375]\",[0.03234593],0.00036011,P2WPKH,sample_mixing_pool,2016-02-16 00:31:19.657,129.221.245.94,18333,residential,BZ,AS49870,Alentus Corp (Proxy Gateway),70015,/Satoshi:22.0.0/\n611959180,2016-02-16 00:31:20,\"[\"\"1Px6fuKhnnw6e4tytg2yHJEMo8MyJ6Uw\"\"]\",\"[\"\"1H6Dj5ZmNzDhPCHNm2ZMQgRSwYj\"\"]\",[0.03234593],[0.0317642],0.00058173,P2WPKH,sample_mixing_pool,2016-02-16 00:31:19.679,129.221.245.94,8333,mobile,BZ,AS49870,Alentus Corp (Proxy Gateway),70015,/Satoshi:22.0.0/\n698602804,2016-02-16 00:31:20,\"[\"\"1H6Dj5ZmNzDhPCHNm2ZMQgRSwYj\"\"]\",\"[\"\"1eydxjs41Pfc16MJtJjkdyxtNTnu\"\"]\",[0.0317642],[0.03139376],0.00037044,P2WPKH,sample_mixing_pool,2016-02-16 00:31:19.675,129.221.245.94,8333,bulletproof_host,BZ,AS49870,Alentus Corp (Proxy Gateway),70015,/Satoshi:0.20.1/\n240783740,2016-02-16 00:31:20,\"[\"\"1eydxjs41Pfc16MJtJjkdyxtNTnu\"\"]\",\"[\"\"1P3eF4baAGBXWAT8hfWGxv2HEnnp\"\"]\",[0.03139376],[0.03096381],0.00042995,P2SH,sample_mixing_pool,2016-02-16 00:31:19.801,129.221.245.94,8333,bulletproof_host,BZ,AS49870,Alentus Corp (Proxy Gateway),70015,/Satoshi:22.0.0/\n397085130,2016-02-16 00:31:20,\"[\"\"1P3eF4baAGBXWAT8hfWGxv2HEnnp\"\"]\",\"[\"\"1NYsLJCca7R9UNHXv37EUJs4uX\"\"]\",[0.03096381],[0.03045258],0.00051123,P2WPKH,sample_mixing_pool,2016-02-16 00:31:19.888,129.221.245.94,8333,residential,BZ,AS49870,Alentus Corp (Proxy Gateway),70015,/Satoshi:0.20.1/\n246386685,2016-02-16 00:31:20,\"[\"\"1NYsLJCca7R9UNHXv37EUJs4uX\"\"]\",\"[\"\"1UPJanW8fxKLUC9Zrv5H2KwBbUL6k\"\"]\",[0.03045258],[0.02965887],0.00079371,P2WPKH,sample_mixing_pool,2016-02-16 00:31:19.606,129.221.245.94,50624,bulletproof_host,BZ,AS49870,Alentus Corp (Proxy Gateway),70015,/Satoshi:22.0.0/\n502037224,2016-02-16 00:31:20,\"[\"\"1UPJanW8fxKLUC9Zrv5H2KwBbUL6k\"\"]\",\"[\"\"1cYmzv6RXENcngYP5Z1uM88VNevjotuqgy\"\"]\",[0.02965887],[0.02887272],0.00078615,P2WPKH,sample_mixing_pool,2016-02-16 00:31:19.801,129.221.245.94,8333,mobile,BZ,AS49870,Alentus Corp (Proxy Gateway),70015,/Satoshi:22.0.0/\n422053777,2016-02-16 00:31:20,\"[\"\"1cYmzv6RXENcngYP5Z1uM88VNevjotuqgy\"\", \"\"1kJ6PYVdCtSFFkpDynkLMCeJBGpzv2h\"\", \"\"1KQRgs93YhA4Sx34kGMWBFwo9kBfm\"\", \"\"1vT3Zndwyi76mf5aZoM7cLGfFJcJsytNxx\"\"]\",\"[\"\"1gFbByw6EzNcj8Y4EbMf8sJ342eZMF8\"\", \"\"1NhE7rsQ4m2ueqGfioRpuGhTa2fhoMD\"\", \"\"1bBGARBKmwTwD8xikWPTTiAebFMcruo\"\", \"\"16C3tzrtej72GKPvCoDi2VXVE451jqAPob\"\", \"\"1no9KgohNfDPsxvk1nHPy1ycThsa4fgbjm\"\", \"\"1QEhYTxNpryaLUD1nBhL1qA8s79g\"\"]\",\"[0.02887272, 0.00281159, 0.00127368, 0.00260571]\",\"[0.0122865, 0.00179391, 0.00238791, 0.01180913, 0.00114696, 0.00539737]\",0.00074192,P2WSH,sample_mixing_pool,2016-02-16 00:31:19.564,129.221.245.94,8333,datacenter,BZ,AS49870,Alentus Corp (Proxy Gateway),70015,/Satoshi:22.0.0/\n430894294,2015-10-16 05:47:25,\"[\"\"1bs5iPLdFjEHkWzFAPTtMZmWAHF\"\"]\",\"[\"\"1GtTjrBX92L5RL4QjKmoeuNbs9cBEYcd\"\"]\",[1572.10555491],[1572.10528742],0.00026749,P2WPKH,sample_licit_commerce,2015-10-16 05:47:24.886,120.144.43.62,59008,datacenter,RU,AS210644,AEZA International LTD,70015,/Satoshi:0.20.1/\n511495908,2015-10-16 05:47:25,\"[\"\"1GtTjrBX92L5RL4QjKmoeuNbs9cBEYcd\"\"]\",\"[\"\"1xB8Dj2FBAXbRT7eQH5nSgtKME1UWusEv\"\", \"\"1UMVbFq2Pxw5qYchFs7XYTux5pdY\"\", \"\"1VibkBxo6dxSbu8JtUWMvG1GPE\"\", \"\"1xT9NrChtpqwQdEwVU4cRBF3TK8wqVef\"\"]\",[1572.10528742],\"[322.95552869, 873.1272622, 339.92347716, 36.09822617]\",0.0007932,P2SH,sample_licit_commerce,2015-10-16 05:47:24.681,120.144.43.62,8333,mobile,RU,AS210644,AEZA International LTD,70015,/Satoshi:0.20.1/\n591937218,2015-10-16 05:47:25,\"[\"\"1xB8Dj2FBAXbRT7eQH5nSgtKME1UWusEv\"\"]\",\"[\"\"1y8R7VY5P132SweHXBVa2GXaZrZqaH\"\"]\",[322.95552869],[322.95499532],0.00053337,P2PKH,sample_licit_commerce,2015-10-16 05:47:24.818,120.144.43.62,8333,mobile,GB,AS2856,British Telecommunications,70015,/Satoshi:21.1.0/\n505199065,2015-10-16 05:47:25,\"[\"\"1UMVbFq2Pxw5qYchFs7XYTux5pdY\"\"]\",\"[\"\"1yTSCa9dPpXBbjfcijpBYxAdvAU8RV\"\", \"\"1HKVPRRXEkoN6RzVbkJp6kjS68Yj3xgAb\"\", \"\"1C7qHcuqnGb6Qiz6rsG73EjW3pPh\"\"]\",[873.1272622],\"[110.65228661, 523.80153197, 238.67267037]\",0.00077325,P2PKH,sample_licit_commerce,2015-10-16 05:47:24.713,139.181.156.109,8333,tor_exit_node,RU,AS210644,AEZA International LTD,70015,/Satoshi:22.0.0/\n282026767,2015-10-16 05:47:25,\"[\"\"1VibkBxo6dxSbu8JtUWMvG1GPE\"\"]\",\"[\"\"1Rwkabd3FWPY3oPXF7EcJYA83iET\"\", \"\"1L8RfHSkdvtbVtRvBcYttqkvSLLX\"\", \"\"1EB3fw14YHPkHtVfs7kbsc1jgM6WLhG\"\", \"\"1NhucNu22XYNgT3QPGkf7wbrqo9wnDw3Vj\"\", \"\"1ufCP4SGyWWfUGrN2mz1UCE7Uwz1GQ7vQx\"\", \"\"1BgEcdu1FyhUYaJwXSv8fAVkJauZQb2z\"\", \"\"1gnaezUF6EbpTpARNt2dBcAKmPY\"\"]\",[339.92347716],\"[15.73531123, 110.75560664, 17.41998495, 18.15967671, 75.14136022, 34.42161368, 68.28951686]\",0.00040687,P2SH,sample_licit_commerce,2015-10-16 05:47:24.813,120.144.43.62,8333,residential,RU,AS210644,AEZA International LTD,70015,/btcd:0.22.0/";

export const TwoStreamUploadView: React.FC<TwoStreamUploadViewProps> = ({ onRunCommand, onClose }) => {
  const [activeTab, setActiveTab] = useState<'DUAL_STREAM' | 'SINGLE_BATCH'>('DUAL_STREAM');
  const [ledgerFile, setLedgerFile] = useState<File | null>(null);
  const [networkFile, setNetworkFile] = useState<File | null>(null);
  const [singleBatchFile, setSingleBatchFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  // Drag-and-drop state indicators
  const [isDraggingZone1, setIsDraggingZone1] = useState(false);
  const [isDraggingZone2, setIsDraggingZone2] = useState(false);
  const [isDraggingBatchZone, setIsDraggingBatchZone] = useState(false);

  const ledgerInputRef = useRef<HTMLInputElement>(null);
  const networkInputRef = useRef<HTMLInputElement>(null);
  const singleBatchInputRef = useRef<HTMLInputElement>(null);

  const handleLoadDemoDualStream = async () => {
    try {
      const pair = await api.getIngestSamplePair();
      if (pair?.ledger_csv && pair?.network_csv) {
        setLedgerFile(new File([pair.ledger_csv], "sample_blockchain_ledger.csv", { type: "text/csv" }));
        setNetworkFile(new File([pair.network_csv], "sample_p2p_network_telemetry.csv", { type: "text/csv" }));
        setError(null);
        sound.playEnterSuccess();
        return;
      }
    } catch {
      // fallback to pre-baked constants
    }
    const lFile = new File([SAMPLE_LEDGER_CSV], "sample_blockchain_ledger.csv", { type: "text/csv" });
    const nFile = new File([SAMPLE_NETWORK_CSV], "sample_p2p_network_telemetry.csv", { type: "text/csv" });
    setLedgerFile(lFile);
    setNetworkFile(nFile);
    setError(null);
    sound.playEnterSuccess();
  };

  const handleLoadDemoSingleBatch = () => {
    const sFile = new File([SAMPLE_SINGLE_BATCH_CSV], "sample_single_batch.csv", { type: "text/csv" });
    setSingleBatchFile(sFile);
    setError(null);
    sound.playEnterSuccess();
  };

  const handleCorrelate = async () => {
    if (!ledgerFile || !networkFile) {
      setError("Both Blockchain Ledger (Stream 1) and Network Telemetry (Stream 2) files are required for dual-stream correlation.");
      sound.playErrorChirp();
      return;
    }
    setError(null);
    setIsUploading(true);
    sound.playEnterSuccess();
    try {
      const res = await api.correlateFiles(ledgerFile, networkFile);
      setResult(res);
      sound.playEnterSuccess();
    } catch (err: any) {
      setError(err.message || 'Correlation failed.');
      sound.playErrorChirp();
    } finally {
      setIsUploading(false);
    }
  };

  const handleSingleBatchUpload = async (fileToUpload?: File | null) => {
    const targetFile = fileToUpload || singleBatchFile;
    if (!targetFile) {
      setError("Please select or drop a bulk ledger file (CSV, JSON, or XML).");
      sound.playErrorChirp();
      return;
    }
    setError(null);
    setIsUploading(true);
    sound.playEnterSuccess();
    try {
      const res = await api.ingestFile(targetFile);
      setResult(res);
      sound.playEnterSuccess();
    } catch (err: any) {
      setError(err.message || 'Single file batch ingestion failed.');
      sound.playErrorChirp();
    } finally {
      setIsUploading(false);
    }
  };

  const getTypologyColor = (typ: string | undefined, isIllicit?: boolean) => {
    if (!isIllicit) return '#00ff66';
    const t = (typ || '').toLowerCase();
    if (t.includes('ransom')) return '#ff3355';
    if (t.includes('peel')) return '#ff8800';
    if (t.includes('layer')) return '#ffcc00';
    if (t.includes('mix')) return '#bb44ff';
    return '#ff4455';
  };

  // Result Summary View
  if (result) {
    const isDualStream = result.matched_records !== undefined;
    const scenarioList = result.scenario_results || [];

    return (
      <div className="output-block" style={{
        background: 'rgba(3, 10, 6, 0.95)',
        border: '1px solid #00aa44',
        boxShadow: '0 0 20px rgba(0, 255, 102, 0.15)',
        padding: '16px',
        marginBottom: '16px',
        borderRadius: '4px',
        fontFamily: 'inherit'
      }}>
        {/* Header Bar */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #005522', paddingBottom: '10px', marginBottom: '14px' }}>
          <div>
            <div style={{ color: '#00ff66', fontWeight: 'bold', fontSize: '15px', letterSpacing: '1px' }}>
              {isDualStream ? '⚡ DUAL-LAYER INGESTION & V8 CORRELATION COMPLETE' : '📁 BULK FILE INGESTION & V8 EVALUATION COMPLETE'}
            </div>
            <div style={{ color: '#88bb99', fontSize: '11px', marginTop: '2px' }}>
              {isDualStream
                ? 'Outer join on txid merged on-chain UTXO state + P2P broadcast telemetry into unified forensic graph.'
                : 'Bulk transaction ledger ingested into in-memory SQLite and scored by XGBoost & Isolation Forest models.'}
            </div>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={() => { setResult(null); sound.playEnterSuccess(); }}
              style={{
                background: 'transparent',
                border: '1px solid #00aa44',
                color: '#33ff88',
                padding: '4px 10px',
                fontSize: '11px',
                cursor: 'pointer',
                fontFamily: 'inherit'
              }}
            >
              [↺ Upload Another File]
            </button>
            {onClose && (
              <button
                onClick={onClose}
                style={{
                  background: 'transparent',
                  border: '1px solid #555',
                  color: '#888',
                  padding: '4px 8px',
                  fontSize: '11px',
                  cursor: 'pointer',
                  fontFamily: 'inherit'
                }}
              >
                [✕]
              </button>
            )}
          </div>
        </div>

        {/* Telemetry Summary Stats */}
        {isDualStream ? (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
            gap: '10px',
            background: 'rgba(0, 25, 10, 0.6)',
            padding: '10px',
            border: '1px solid #00441a',
            marginBottom: '16px',
            fontSize: '12px'
          }}>
            <div>
              <div style={{ color: '#66aa88', fontSize: '10px' }}>LEDGER TXS</div>
              <div style={{ color: '#fff', fontSize: '16px', fontWeight: 'bold' }}>{result.ledger_records}</div>
            </div>
            <div>
              <div style={{ color: '#66aa88', fontSize: '10px' }}>P2P TELEMETRY TXS</div>
              <div style={{ color: '#fff', fontSize: '16px', fontWeight: 'bold' }}>{result.network_records}</div>
            </div>
            <div>
              <div style={{ color: '#66aa88', fontSize: '10px' }}>CORRELATION MATCH</div>
              <div style={{ color: '#33ff88', fontSize: '16px', fontWeight: 'bold' }}>
                {result.matched_records} ({(result.correlation_rate * 100).toFixed(1)}%)
              </div>
            </div>
            <div>
              <div style={{ color: '#66aa88', fontSize: '10px' }}>NEWLY INDEXED</div>
              <div style={{ color: '#aaffaa', fontSize: '16px', fontWeight: 'bold' }}>{result.newly_indexed_records}</div>
            </div>
            <div>
              <div style={{ color: '#66aa88', fontSize: '10px' }}>UNMATCHED STREAMS</div>
              <div style={{ color: '#ffaa33', fontSize: '16px', fontWeight: 'bold' }}>{(result.unmatched_ledger || 0) + (result.unmatched_network || 0)}</div>
            </div>
          </div>
        ) : (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
            gap: '10px',
            background: 'rgba(0, 25, 10, 0.6)',
            padding: '10px',
            border: '1px solid #00441a',
            marginBottom: '16px',
            fontSize: '12px'
          }}>
            <div>
              <div style={{ color: '#66aa88', fontSize: '10px' }}>TOTAL INGESTED</div>
              <div style={{ color: '#fff', fontSize: '16px', fontWeight: 'bold' }}>{result.total_ingested ?? result.input_records}</div>
            </div>
            <div>
              <div style={{ color: '#66aa88', fontSize: '10px' }}>UNIQUE RECORDS</div>
              <div style={{ color: '#fff', fontSize: '16px', fontWeight: 'bold' }}>{result.unique_records}</div>
            </div>
            <div>
              <div style={{ color: '#66aa88', fontSize: '10px' }}>NEWLY INDEXED</div>
              <div style={{ color: '#33ff88', fontSize: '16px', fontWeight: 'bold' }}>{result.newly_indexed_records}</div>
            </div>
            <div>
              <div style={{ color: '#66aa88', fontSize: '10px' }}>DUPLICATE TXS</div>
              <div style={{ color: '#ffaa33', fontSize: '16px', fontWeight: 'bold' }}>{result.duplicate_records}</div>
            </div>
            <div>
              <div style={{ color: '#66aa88', fontSize: '10px' }}>WALLETS ADDED</div>
              <div style={{ color: '#aaffaa', fontSize: '16px', fontWeight: 'bold' }}>+{result.unique_wallets_added ?? 0}</div>
            </div>
          </div>
        )}

        {/* Scenarios Analyzed */}
        <div style={{ color: '#33ff88', fontWeight: 'bold', fontSize: '13px', marginBottom: '8px', letterSpacing: '0.5px' }}>
          [*] V8 MACHINE LEARNING THREAT EVALUATION ({scenarioList.length} Scenario Clusters)
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {scenarioList.map((sc: any, idx: number) => {
            const isAvail = sc.analysis_status === 'AVAILABLE';
            const riskPct = sc.risk_score !== null && sc.risk_score !== undefined ? (sc.risk_score * 100).toFixed(1) : 'N/A';
            const isIllicit = Boolean(sc.is_illicit);
            const typ = sc.predicted_typology || (isIllicit ? 'UNKNOWN' : 'NORMAL');
            const typColor = getTypologyColor(typ, isIllicit);
            const typConfPct = sc.typology_confidence !== null && sc.typology_confidence !== undefined ? (sc.typology_confidence * 100).toFixed(1) : null;
            const anomScore = sc.anomaly_score !== null && sc.anomaly_score !== undefined ? Number(sc.anomaly_score).toFixed(1) : null;

            return (
              <div
                key={sc.scenario_id || idx}
                style={{
                  background: 'rgba(5, 18, 10, 0.85)',
                  border: `1px solid ${typColor}`,
                  borderRadius: '3px',
                  padding: '12px',
                  boxShadow: `0 0 10px ${typColor}22`
                }}
              >
                {/* Scenario Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px', marginBottom: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{
                      background: `${typColor}22`,
                      color: typColor,
                      border: `1px solid ${typColor}`,
                      padding: '2px 8px',
                      fontSize: '11px',
                      fontWeight: 'bold',
                      borderRadius: '2px'
                    }}>
                      {isIllicit ? `⚠️ ${typ.toUpperCase()} THREAT` : '🛡️ LICIT ACTIVITY'}
                    </span>
                    <span style={{ color: '#ffffff', fontWeight: 'bold', fontSize: '14px' }}>
                      Scenario: {sc.scenario_id}
                    </span>
                    <span style={{ color: '#888', fontSize: '11px' }}>
                      ({sc.transaction_count} transactions)
                    </span>
                  </div>

                  <div style={{ display: 'flex', gap: '8px' }}>
                    {onRunCommand && (
                      <>
                        <button
                          onClick={() => { sound.playEnterSuccess(); onRunCommand(`graph ${sc.scenario_id}`); }}
                          style={{
                            background: '#003311',
                            border: '1px solid #00ff66',
                            color: '#00ff66',
                            padding: '3px 9px',
                            fontSize: '11px',
                            cursor: 'pointer',
                            fontWeight: 'bold',
                            fontFamily: 'inherit'
                          }}
                        >
                          🌐 Open in 3D Graph
                        </button>
                        <button
                          onClick={() => { sound.playEnterSuccess(); onRunCommand(`inspect ${sc.scenario_id}`); }}
                          style={{
                            background: 'transparent',
                            border: '1px solid #00aa44',
                            color: '#33ff88',
                            padding: '3px 8px',
                            fontSize: '11px',
                            cursor: 'pointer',
                            fontFamily: 'inherit'
                          }}
                        >
                          🔍 Inspect
                        </button>
                      </>
                    )}
                  </div>
                </div>

                {isAvail ? (
                  <>
                    {/* Metrics Bar */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '10px', marginTop: '8px', fontSize: '12px' }}>
                      <div style={{ background: 'rgba(0,0,0,0.4)', padding: '8px', borderLeft: `3px solid ${typColor}` }}>
                        <div style={{ color: '#888', fontSize: '10px' }}>V8 BINARY RISK SCORE P(illicit)</div>
                        <div style={{ color: typColor, fontSize: '15px', fontWeight: 'bold' }}>{riskPct}%</div>
                        <div style={{ width: '100%', height: '4px', background: '#222', marginTop: '4px', borderRadius: '2px', overflow: 'hidden' }}>
                          <div style={{ width: `${Math.min(100, Math.max(0, Number(riskPct)))}%`, height: '100%', background: typColor }} />
                        </div>
                      </div>

                      {typConfPct && (
                        <div style={{ background: 'rgba(0,0,0,0.4)', padding: '8px', borderLeft: '3px solid #ffaa00' }}>
                          <div style={{ color: '#888', fontSize: '10px' }}>TYPOLOGY CONFIDENCE</div>
                          <div style={{ color: '#ffaa00', fontSize: '15px', fontWeight: 'bold' }}>{typConfPct}% ({typ.toUpperCase()})</div>
                          <div style={{ width: '100%', height: '4px', background: '#222', marginTop: '4px', borderRadius: '2px', overflow: 'hidden' }}>
                            <div style={{ width: `${Math.min(100, Math.max(0, Number(typConfPct)))}%`, height: '100%', background: '#ffaa00' }} />
                          </div>
                        </div>
                      )}

                      {anomScore !== null && (
                        <div style={{ background: 'rgba(0,0,0,0.4)', padding: '8px', borderLeft: '3px solid #33bbff' }}>
                          <div style={{ color: '#888', fontSize: '10px' }}>ISOLATION FOREST ANOMALY (0–100)</div>
                          <div style={{ color: Number(anomScore) >= 70 ? '#ff4455' : '#33bbff', fontSize: '15px', fontWeight: 'bold' }}>
                            {anomScore} <span style={{ fontSize: '11px', fontWeight: 'normal' }}>[{sc.anomaly_label || 'NORMAL'}]</span>
                          </div>
                          <div style={{ width: '100%', height: '4px', background: '#222', marginTop: '4px', borderRadius: '2px', overflow: 'hidden' }}>
                            <div style={{ width: `${Math.min(100, Math.max(0, Number(anomScore)))}%`, height: '100%', background: Number(anomScore) >= 70 ? '#ff4455' : '#33bbff' }} />
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Typology Explanation */}
                    {sc.typology_explanation && (
                      <div style={{ marginTop: '10px', fontSize: '12px', color: '#cce6d0', background: 'rgba(0, 30, 15, 0.5)', padding: '8px', borderLeft: '2px solid #00ff66' }}>
                        <strong style={{ color: '#33ff88' }}>Forensic Typology Rationale:</strong> {sc.typology_explanation}
                      </div>
                    )}

                    {/* SHAP Feature Attributions */}
                    {sc.top_shap_attributions && sc.top_shap_attributions.length > 0 && (
                      <div style={{ marginTop: '10px' }}>
                        <div style={{ fontSize: '11px', color: '#88bb99', fontWeight: 'bold', marginBottom: '4px' }}>
                          KEY XGBOOST TREESHAP INFLUENCE FACTORS:
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '6px' }}>
                          {sc.top_shap_attributions.slice(0, 4).map((attr: any, aIdx: number) => {
                            const isElev = attr.direction === 'ELEVATES_RISK' || attr.direction === 'RISK_INCREASING';
                            return (
                              <div
                                key={aIdx}
                                style={{
                                  background: 'rgba(0,0,0,0.5)',
                                  padding: '5px 8px',
                                  fontSize: '11px',
                                  display: 'flex',
                                  justifyContent: 'space-between',
                                  alignItems: 'center',
                                  borderLeft: `2px solid ${isElev ? '#ff5544' : '#00ff66'}`
                                }}
                              >
                                <span style={{ color: '#ddd' }}>{attr.plain_name || attr.feature_name}</span>
                                <span style={{ color: isElev ? '#ff6655' : '#33ff88', fontWeight: 'bold' }}>
                                  {isElev ? '▲ +' : '▼ -'}{Math.abs(Number(attr.attribution_value || attr.shap_value || 0)).toFixed(3)}
                                </span>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}
                  </>
                ) : (
                  <div style={{ color: '#ffbb44', fontSize: '12px', marginTop: '6px', fontStyle: 'italic' }}>
                    {sc.analysis_message || 'ML model evaluation pending or unavailable for this sample size.'}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  // Pre-upload Staging View
  return (
    <div className="output-block" style={{
      background: 'rgba(2, 8, 4, 0.95)',
      border: '1px solid #00aa44',
      padding: '16px',
      marginTop: '10px',
      marginBottom: '16px',
      borderRadius: '4px',
      boxShadow: '0 0 20px rgba(0, 255, 102, 0.1)'
    }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #005522', paddingBottom: '10px', marginBottom: '14px' }}>
        <div>
          <div style={{ color: '#00ff66', fontWeight: 'bold', fontSize: '15px', letterSpacing: '1px' }}>
            ⚡ BITKAUN FORENSIC DATA INGESTION &amp; ML CORRELATION (V8)
          </div>
          <div style={{ color: '#88bb99', fontSize: '11px', marginTop: '2px' }}>
            Drag and drop or select files to ingest into in-memory SQLite and run live XGBoost &amp; Isolation Forest threat scoring.
          </div>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: '1px solid #555',
              color: '#888',
              padding: '3px 8px',
              fontSize: '11px',
              cursor: 'pointer',
              fontFamily: 'inherit'
            }}
          >
            [✕]
          </button>
        )}
      </div>

      {/* Mode Selector Tabs */}
      <div style={{ display: 'flex', gap: '10px', marginBottom: '16px' }}>
        <button
          onClick={() => { setActiveTab('DUAL_STREAM'); setError(null); sound.playKeyClick(); }}
          style={{
            flex: 1,
            background: activeTab === 'DUAL_STREAM' ? '#00441a' : 'rgba(0, 20, 10, 0.5)',
            border: activeTab === 'DUAL_STREAM' ? '1px solid #00ff66' : '1px solid #00441a',
            color: activeTab === 'DUAL_STREAM' ? '#00ff66' : '#88aa99',
            padding: '8px 12px',
            fontSize: '12px',
            fontWeight: 'bold',
            cursor: 'pointer',
            fontFamily: 'inherit',
            borderRadius: '2px',
            transition: 'all 0.15s ease'
          }}
        >
          ⚡ Dual-Stream Correlation (Ledger + P2P Network Outer Join)
        </button>
        <button
          onClick={() => { setActiveTab('SINGLE_BATCH'); setError(null); sound.playKeyClick(); }}
          style={{
            flex: 1,
            background: activeTab === 'SINGLE_BATCH' ? '#00441a' : 'rgba(0, 20, 10, 0.5)',
            border: activeTab === 'SINGLE_BATCH' ? '1px solid #00ff66' : '1px solid #00441a',
            color: activeTab === 'SINGLE_BATCH' ? '#00ff66' : '#88aa99',
            padding: '8px 12px',
            fontSize: '12px',
            fontWeight: 'bold',
            cursor: 'pointer',
            fontFamily: 'inherit',
            borderRadius: '2px',
            transition: 'all 0.15s ease'
          }}
        >
          📁 Single-File Batch Ingest (Combined CSV / JSON / XML)
        </button>
      </div>

      {/* DUAL STREAM TAB */}
      {activeTab === 'DUAL_STREAM' && (
        <>
          {/* 1-Click Demo Preset Banner */}
          <div style={{
            background: 'rgba(0, 35, 15, 0.7)',
            border: '1px dashed #00cc55',
            padding: '10px 14px',
            marginBottom: '16px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            borderRadius: '3px'
          }}>
            <div style={{ fontSize: '12px', color: '#cce6d0' }}>
              <strong style={{ color: '#33ff88' }}>[BENCHMARK PRESET]:</strong> Want to test dual-layer correlation instantly without manual CSVs?
            </div>
            <button
              onClick={handleLoadDemoDualStream}
              style={{
                background: '#00441a',
                border: '1px solid #00ff66',
                color: '#00ff66',
                padding: '5px 12px',
                fontSize: '11px',
                fontWeight: 'bold',
                cursor: 'pointer',
                fontFamily: 'inherit',
                borderRadius: '2px'
              }}
            >
              ⚡ Load Sample Dual-Stream Pair
            </button>
          </div>

          {/* Dual Upload Zones with Drag-and-Drop */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px', marginBottom: '16px' }}>
            {/* ZONE 1: Blockchain Ledger */}
            <div
              onDragEnter={(e) => { e.preventDefault(); e.stopPropagation(); setIsDraggingZone1(true); }}
              onDragOver={(e) => { e.preventDefault(); e.stopPropagation(); setIsDraggingZone1(true); }}
              onDragLeave={(e) => { e.preventDefault(); e.stopPropagation(); setIsDraggingZone1(false); }}
              onDrop={(e) => {
                e.preventDefault();
                e.stopPropagation();
                setIsDraggingZone1(false);
                if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                  setLedgerFile(e.dataTransfer.files[0]);
                  setError(null);
                  sound.playKeyClick();
                }
              }}
              style={{
                border: isDraggingZone1
                  ? '2px dashed #33ff88'
                  : ledgerFile
                    ? '1px solid #00ff66'
                    : '1px dashed #008833',
                background: isDraggingZone1
                  ? 'rgba(0, 60, 25, 0.6)'
                  : ledgerFile
                    ? 'rgba(0, 40, 18, 0.4)'
                    : 'rgba(0, 15, 8, 0.6)',
                padding: '18px',
                textAlign: 'center',
                cursor: 'pointer',
                borderRadius: '3px',
                transition: 'all 0.2s ease',
                boxShadow: isDraggingZone1 ? '0 0 15px rgba(0, 255, 102, 0.4)' : 'none'
              }}
              onClick={() => ledgerInputRef.current?.click()}
            >
              <div style={{ color: '#00ff66', fontWeight: 'bold', fontSize: '13px', letterSpacing: '1px' }}>
                ZONE 1: ON-CHAIN BLOCKCHAIN LEDGER
              </div>
              <div style={{ color: '#fff', fontSize: '12px', marginTop: '4px' }}>
                UTXO Inputs / Outputs, Amounts &amp; Fees
              </div>
              <div style={{ fontSize: '11px', color: '#77aa88', marginTop: '4px' }}>
                Accepts CSV, JSON, or XML format
              </div>

              <input
                type="file"
                ref={ledgerInputRef}
                style={{ display: 'none' }}
                accept=".csv,.json,.xml,text/csv,application/json,application/xml,text/xml"
                onClick={(e) => e.stopPropagation()}
                onChange={(e) => {
                  if (e.target.files?.[0]) {
                    setLedgerFile(e.target.files[0]);
                    setError(null);
                    sound.playKeyClick();
                  }
                }}
              />

              {ledgerFile ? (
                <div style={{ marginTop: '12px', padding: '6px', background: '#003311', border: '1px solid #00ff66', color: '#aaffaa', fontSize: '12px' }}>
                  ✓ Loaded: <strong>{ledgerFile.name}</strong> ({(ledgerFile.size / 1024).toFixed(1)} KB)
                  <button
                    onClick={(e) => { e.stopPropagation(); setLedgerFile(null); }}
                    style={{ marginLeft: '8px', background: 'transparent', border: 'none', color: '#ff6666', cursor: 'pointer' }}
                  >
                    [✕]
                  </button>
                </div>
              ) : (
                <div style={{ marginTop: '12px', color: isDraggingZone1 ? '#33ff88' : '#558866', fontSize: '11px', fontWeight: isDraggingZone1 ? 'bold' : 'normal' }}>
                  {isDraggingZone1 ? '⬇ Drop Ledger CSV File Here' : '[ Click or Drag & Drop Ledger CSV Here ]'}
                </div>
              )}
            </div>

            {/* ZONE 2: P2P Network Telemetry */}
            <div
              onDragEnter={(e) => { e.preventDefault(); e.stopPropagation(); setIsDraggingZone2(true); }}
              onDragOver={(e) => { e.preventDefault(); e.stopPropagation(); setIsDraggingZone2(true); }}
              onDragLeave={(e) => { e.preventDefault(); e.stopPropagation(); setIsDraggingZone2(false); }}
              onDrop={(e) => {
                e.preventDefault();
                e.stopPropagation();
                setIsDraggingZone2(false);
                if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                  setNetworkFile(e.dataTransfer.files[0]);
                  setError(null);
                  sound.playKeyClick();
                }
              }}
              style={{
                border: isDraggingZone2
                  ? '2px dashed #33ff88'
                  : networkFile
                    ? '1px solid #00ff66'
                    : '1px dashed #008833',
                background: isDraggingZone2
                  ? 'rgba(0, 60, 25, 0.6)'
                  : networkFile
                    ? 'rgba(0, 40, 18, 0.4)'
                    : 'rgba(0, 15, 8, 0.6)',
                padding: '18px',
                textAlign: 'center',
                cursor: 'pointer',
                borderRadius: '3px',
                transition: 'all 0.2s ease',
                boxShadow: isDraggingZone2 ? '0 0 15px rgba(0, 255, 102, 0.4)' : 'none'
              }}
              onClick={() => networkInputRef.current?.click()}
            >
              <div style={{ color: '#00ff66', fontWeight: 'bold', fontSize: '13px', letterSpacing: '1px' }}>
                ZONE 2: OFF-CHAIN P2P NETWORK TELEMETRY
              </div>
              <div style={{ color: '#fff', fontSize: '12px', marginTop: '4px' }}>
                Relay IPs, ASNs, Ports, ISPs &amp; Latency Delays
              </div>
              <div style={{ fontSize: '11px', color: '#77aa88', marginTop: '4px' }}>
                Accepts CSV, JSON, or XML format
              </div>

              <input
                type="file"
                ref={networkInputRef}
                style={{ display: 'none' }}
                accept=".csv,.json,.xml,text/csv,application/json,application/xml,text/xml"
                onClick={(e) => e.stopPropagation()}
                onChange={(e) => {
                  if (e.target.files?.[0]) {
                    setNetworkFile(e.target.files[0]);
                    setError(null);
                    sound.playKeyClick();
                  }
                }}
              />

              {networkFile ? (
                <div style={{ marginTop: '12px', padding: '6px', background: '#003311', border: '1px solid #00ff66', color: '#aaffaa', fontSize: '12px' }}>
                  ✓ Loaded: <strong>{networkFile.name}</strong> ({(networkFile.size / 1024).toFixed(1)} KB)
                  <button
                    onClick={(e) => { e.stopPropagation(); setNetworkFile(null); }}
                    style={{ marginLeft: '8px', background: 'transparent', border: 'none', color: '#ff6666', cursor: 'pointer' }}
                  >
                    [✕]
                  </button>
                </div>
              ) : (
                <div style={{ marginTop: '12px', color: isDraggingZone2 ? '#33ff88' : '#558866', fontSize: '11px', fontWeight: isDraggingZone2 ? 'bold' : 'normal' }}>
                  {isDraggingZone2 ? '⬇ Drop Network CSV File Here' : '[ Click or Drag & Drop Network Telemetry CSV Here ]'}
                </div>
              )}
            </div>
          </div>

          {/* Quick Helper if only 1 file is loaded in Dual Stream mode */}
          {ledgerFile && !networkFile && (
            <div style={{
              background: 'rgba(0, 30, 20, 0.7)',
              border: '1px solid #008844',
              padding: '8px 12px',
              marginBottom: '14px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              fontSize: '11px',
              color: '#88ccaa'
            }}>
              <span>Ledger file loaded. Ingest directly as a single stream or drop Zone 2 network telemetry to correlate.</span>
              <button
                onClick={() => handleSingleBatchUpload(ledgerFile)}
                disabled={isUploading}
                style={{
                  background: '#00441a',
                  border: '1px solid #00aa44',
                  color: '#33ff88',
                  padding: '4px 10px',
                  fontSize: '11px',
                  fontWeight: 'bold',
                  cursor: 'pointer',
                  fontFamily: 'inherit'
                }}
              >
                Ingest Ledger Alone ➔
              </button>
            </div>
          )}

          {error && (
            <div style={{
              color: '#ff4455',
              background: 'rgba(40, 0, 10, 0.7)',
              border: '1px solid #ff3344',
              padding: '8px 12px',
              marginBottom: '14px',
              fontSize: '12px',
              borderRadius: '2px'
            }}>
              ⚠️ {error}
            </div>
          )}

          {/* Action Button */}
          <div style={{ textAlign: 'center' }}>
            <button
              onClick={handleCorrelate}
              disabled={isUploading || (!ledgerFile || !networkFile)}
              style={{
                background: isUploading
                  ? '#003311'
                  : (!ledgerFile || !networkFile)
                    ? '#052210'
                    : '#00ff66',
                color: (!ledgerFile || !networkFile) ? '#446655' : '#030805',
                border: (!ledgerFile || !networkFile) ? '1px solid #004422' : 'none',
                padding: '12px 28px',
                fontSize: '13px',
                fontWeight: 'bold',
                letterSpacing: '1px',
                cursor: isUploading ? 'wait' : (!ledgerFile || !networkFile) ? 'not-allowed' : 'pointer',
                fontFamily: 'inherit',
                boxShadow: (ledgerFile && networkFile) ? '0 0 15px rgba(0, 255, 102, 0.3)' : 'none',
                borderRadius: '2px',
                transition: 'all 0.2s ease'
              }}
            >
              {isUploading
                ? '⚡ MERGING DUAL STREAMS & RUNNING V8 ML INFERENCE...'
                : '[ MERGE DUAL STREAMS & RUN V8 ML INFERENCE ]'}
            </button>
          </div>
        </>
      )}

      {/* SINGLE BATCH TAB */}
      {activeTab === 'SINGLE_BATCH' && (
        <>
          {/* Demo Preset Banner */}
          <div style={{
            background: 'rgba(0, 35, 15, 0.7)',
            border: '1px dashed #00cc55',
            padding: '10px 14px',
            marginBottom: '16px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            borderRadius: '3px'
          }}>
            <div style={{ fontSize: '12px', color: '#cce6d0' }}>
              <strong style={{ color: '#33ff88' }}>[SAMPLE BATCH]:</strong> Ingest realistic synthetic transactions with pre-joined telemetry.
            </div>
            <button
              onClick={handleLoadDemoSingleBatch}
              style={{
                background: '#00441a',
                border: '1px solid #00ff66',
                color: '#00ff66',
                padding: '5px 12px',
                fontSize: '11px',
                fontWeight: 'bold',
                cursor: 'pointer',
                fontFamily: 'inherit',
                borderRadius: '2px'
              }}
            >
              📁 Load Sample Batch File
            </button>
          </div>

          {/* Single Drop Zone with Drag-and-Drop */}
          <div
            onDragEnter={(e) => { e.preventDefault(); e.stopPropagation(); setIsDraggingBatchZone(true); }}
            onDragOver={(e) => { e.preventDefault(); e.stopPropagation(); setIsDraggingBatchZone(true); }}
            onDragLeave={(e) => { e.preventDefault(); e.stopPropagation(); setIsDraggingBatchZone(false); }}
            onDrop={(e) => {
              e.preventDefault();
              e.stopPropagation();
              setIsDraggingBatchZone(false);
              if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                setSingleBatchFile(e.dataTransfer.files[0]);
                setError(null);
                sound.playKeyClick();
              }
            }}
            style={{
              border: isDraggingBatchZone
                ? '2px dashed #33ff88'
                : singleBatchFile
                  ? '1px solid #00ff66'
                  : '1px dashed #008833',
              background: isDraggingBatchZone
                ? 'rgba(0, 60, 25, 0.6)'
                : singleBatchFile
                  ? 'rgba(0, 40, 18, 0.4)'
                  : 'rgba(0, 15, 8, 0.6)',
              padding: '28px',
              textAlign: 'center',
              cursor: 'pointer',
              borderRadius: '3px',
              marginBottom: '16px',
              transition: 'all 0.2s ease',
              boxShadow: isDraggingBatchZone ? '0 0 15px rgba(0, 255, 102, 0.4)' : 'none'
            }}
            onClick={() => singleBatchInputRef.current?.click()}
          >
            <div style={{ color: '#00ff66', fontWeight: 'bold', fontSize: '14px', letterSpacing: '1px' }}>
              BULK TRANSACTION &amp; TELEMETRY FILE
            </div>
            <div style={{ color: '#fff', fontSize: '12px', marginTop: '6px' }}>
              Multi-input/output ledger and optional network metadata in a single file
            </div>
            <div style={{ fontSize: '11px', color: '#77aa88', marginTop: '4px' }}>
              Accepts <strong>.csv</strong>, <strong>.json</strong>, or <strong>.xml</strong> formats
            </div>

            <input
              type="file"
              ref={singleBatchInputRef}
              style={{ display: 'none' }}
              accept=".csv,.json,.xml,text/csv,application/json,application/xml,text/xml"
              onClick={(e) => e.stopPropagation()}
              onChange={(e) => {
                if (e.target.files?.[0]) {
                  setSingleBatchFile(e.target.files[0]);
                  setError(null);
                  sound.playKeyClick();
                }
              }}
            />

            {singleBatchFile ? (
              <div style={{ marginTop: '16px', padding: '8px', background: '#003311', border: '1px solid #00ff66', color: '#aaffaa', fontSize: '13px', display: 'inline-block' }}>
                ✓ Loaded: <strong>{singleBatchFile.name}</strong> ({(singleBatchFile.size / 1024).toFixed(1)} KB)
                <button
                  onClick={(e) => { e.stopPropagation(); setSingleBatchFile(null); }}
                  style={{ marginLeft: '10px', background: 'transparent', border: 'none', color: '#ff6666', cursor: 'pointer' }}
                >
                  [✕]
                </button>
              </div>
            ) : (
              <div style={{ marginTop: '16px', color: isDraggingBatchZone ? '#33ff88' : '#558866', fontSize: '12px', fontWeight: isDraggingBatchZone ? 'bold' : 'normal' }}>
                {isDraggingBatchZone ? '⬇ Drop Transaction File Here' : '[ Click or Drag & Drop Bulk File Here ]'}
              </div>
            )}
          </div>

          {error && (
            <div style={{
              color: '#ff4455',
              background: 'rgba(40, 0, 10, 0.7)',
              border: '1px solid #ff3344',
              padding: '8px 12px',
              marginBottom: '14px',
              fontSize: '12px',
              borderRadius: '2px'
            }}>
              ⚠️ {error}
            </div>
          )}

          {/* Action Button */}
          <div style={{ textAlign: 'center' }}>
            <button
              onClick={() => handleSingleBatchUpload()}
              disabled={isUploading || !singleBatchFile}
              style={{
                background: isUploading
                  ? '#003311'
                  : !singleBatchFile
                    ? '#052210'
                    : '#00ff66',
                color: !singleBatchFile ? '#446655' : '#030805',
                border: !singleBatchFile ? '1px solid #004422' : 'none',
                padding: '12px 28px',
                fontSize: '13px',
                fontWeight: 'bold',
                letterSpacing: '1px',
                cursor: isUploading ? 'wait' : !singleBatchFile ? 'not-allowed' : 'pointer',
                fontFamily: 'inherit',
                boxShadow: singleBatchFile ? '0 0 15px rgba(0, 255, 102, 0.3)' : 'none',
                borderRadius: '2px',
                transition: 'all 0.2s ease'
              }}
            >
              {isUploading
                ? '📁 INGESTING BULK FILE & COMPUTING ML SCORES...'
                : '[ INGEST BATCH & RUN V8 SCENARIO ANALYSIS ]'}
            </button>
          </div>
        </>
      )}
    </div>
  );
};
