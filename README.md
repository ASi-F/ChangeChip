# ChangeChip

This repository was forked from [here](https://github.com/Scientific-Computing-Lab-NRCN/ChangeChip).


## Requirements:
- Download the DEXTR model (for the optinal cropping stage):
```
cd DEXTR/models/
chmod +x download_dextr_model.sh
./download_dextr_model.sh
cd ../..
```
- Conda Requirements:

Building environment from ```yml``` file:

```conda env create --name envname --file=conda_changechip.yml```

Or, create a new conda environment with python 3.6:
```
conda create -n envname python=3.6
```

and Install the following packages:
```
conda install pytorch torchvision -c pytorch
conda install numpy scipy matplotlib
conda install opencv pillow scikit-learn scikit-image
conda install keras tensorflow
conda install seaborn
```

## Running:
- Run the following command under the conda environment with your spesific directory and images paths, and change the values of the system parameters, if needed.
```
python Scripts/main.py -output_dir Example/Output 
-input_path Example/INPUT_IMAGE.JPG 
-reference_path Example/REFERENCE_IMAGE.JPG 
-n 16 
-window_size 5 
-pca_dim_gray 3
-pca_dim_rgb 9
-resize_factor 1
-lighting_fix
-use_homography
-save_extra_stuff
```
You can either run ```./run_exmaple.sh```.
