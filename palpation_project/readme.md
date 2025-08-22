v1 currently works for VCA trace and sweep

    Workflow:
        0. open the v1 folder
        1. set the desired parameters in config.py
        2. make the kuka TCP vertical and position it roughly at 0,0 for your sample
            (make sure it is above the highest point on the surface with the VCA extended)
        3. run the TCP_vca_sweep program on kuka in AUT mode
        4. run main.py and follow the prompts
            make sure the computer's wifi is connected to the labview laptop hotspot
        5. start the labview code
        6. press Enter to begin trace
        7. wait for trace to complete
        8. press Enter to begin sweep
        9. switch labview program to sweep mode

    tldr workflow:
        - (set config / position kuka)
        - start kuka
        - start python
        - start labview
        - switch to sweep after trace done

v0 is deprecated - don't use it
