import sys
sys.path.append('/home/yonif/.conda/envs/pca_kmeans_change_detection/lib/python3.6/site-packages')
import numpy as np
np.set_printoptions(threshold=sys.maxsize)
import cv2
import time
from PCA_Kmeans import compute_change_map, find_group_of_accepted_classes_DBSCAN, draw_combination_on_transparent_input_image
import global_variables
import os
import argparse
import bounding_box

def main(output_dir, input_path, reference_path, n, use_first, window_size, pca_dim_rgb, pca_dim_hsv,
         cut, lighting_fix, use_homography, resize_factor, save_extra_stuff, shade_boxes):
    '''

    :param output_dir: destination directory for the output
    :param input_path: path to the input image
    :param reference_path: path to the reference image
    :param n: number of classes for clustering the diff descriptors
    :param use_first: number of classes with the highest mse scores to be slassified as defective
    :param window_size: window size for the diff descriptors
    :param pca_dim_rgb: pca target dimension for the rgb diff descriptor
    :param pca_dim_hsv: pca target dimension for the hsv diff descriptor
    :param cut: true to enable DXTR cropping
    :param lighting_fix: true to enable histogram matching
    :param use_homography: true to enable SIFT homography (always recommended)
    :param resize_factor: scale the input images, usually with factor smaller than 1 for faster results
    :param save_extra_stuff: save diagnostics and extra results, usually for debugging
    :param shade_boxes: give bboxes of classes with hogher mse scores shades closer to red and with lesser score shades closer to blue
    '''
    global_variables.init(output_dir, save_extra_stuff) #setting global variables

    if use_homography:
        from registration import homography
    if lighting_fix:
        from light_differences_elimination import light_diff_elimination


    #for time estimations
    start_time = time.time()

    #read the inputs
    image_1 = cv2.imread(input_path, 1)
    image_2 = cv2.imread(reference_path, 1)

    #we need the images to be the same size. resize_factor is for increasing or decreasing further the images
    new_shape = (int(resize_factor*0.5*(image_1.shape[1]+image_2.shape[1])), int(resize_factor*0.5*(image_1.shape[0]+image_2.shape[0])))
    image_1 = cv2.resize(image_1,new_shape, interpolation=cv2.INTER_AREA)
    image_2 = cv2.resize(image_2, new_shape, interpolation=cv2.INTER_AREA)
    global_variables.set_size(new_shape[0],new_shape[1])
    if cut:
        import crop
        image_1, image_2, result_1, result_2 = crop.crop_images(image_1, image_2)
        mask = np.zeros((result_2.shape[0], result_2.shape[1], 3), dtype=np.uint8)
        for i in range(image_2.shape[:2][0]):
            for j in range(image_2.shape[:2][1]):
                if result_2[i][j] == True:
                    mask[i][j] = [255, 255, 255]
        if use_homography:
            image2_registered, mask_registered, blank_pixels = homography(cut, image_1, image_2, mask)
        else:
            image2_registered  = image_2
        min_width = min(image_1.shape[:2][0], image_2.shape[:2][0])
        min_height = min(image_1.shape[:2][1], image_2.shape[:2][1])
        for i in range(min_width):
            for j in range(min_height):
                if result_1[i][j] == False:
                    image2_registered[i][j] = 0
                    image_1[i][j] = 0
        if use_homography:
            for i in range(min_width):
                for j in range(min_height):
                        if mask_registered[i][j][0] == 0:
                            image2_registered[i][j] = 0
                            image_1[i][j] = 0

        cv2.imwrite(global_variables.output_dir + '/blanked_1.jpg', image_1)
        cv2.imwrite(global_variables.output_dir + '/blanked_2.jpg', image2_registered)
    else:
        if use_homography:
            image2_registered, mask_registered, blank_pixels = homography(cut, image_1, image_2, None)
        else:
            image2_registered  = image_2

    if use_homography:
        image_1[blank_pixels] = [0,0,0]
        image2_registered[blank_pixels] = [0, 0, 0]

    if (global_variables.save_extra_stuff):
        cv2.imwrite(global_variables.output_dir+ '/resized_blanked_1.jpg', image_1)

    if (lighting_fix):
        #Using the histogram matching, only image2_registered is changed
        image2_registered = light_diff_elimination(image_1, image2_registered)
        cv2.imwrite(global_variables.output_dir + '/image2_registered.jpg', image2_registered)
        print("--- Preprocessing time - %s seconds ---" % (time.time() - start_time))


    start_time = time.time()
    clustering_map, mse_array, size_array = compute_change_map(image_1, image2_registered, window_size=window_size,
                                                               clusters=n, pca_dim_rgb=pca_dim_rgb, pca_dim_hsv=pca_dim_hsv)

    clustering = [[] for _ in range(n)]
    for i in range(clustering_map.shape[0]):
        for j in range(clustering_map.shape[1]):
            clustering[int(clustering_map[i,j])].append([i,j])

    input_image = cv2.imread(input_path)
    input_image = cv2.resize(input_image,new_shape, interpolation=cv2.INTER_AREA)
    b_channel, g_channel, r_channel = cv2.split(input_image)
    alpha_channel = np.ones(b_channel.shape, dtype=b_channel.dtype) * 255
    alpha_channel[:, :] = 50
    if use_first == -1:
        groups = find_group_of_accepted_classes_DBSCAN(mse_array)
    else:
        npmse = np.array(mse_array)
        groups = [npmse.argsort()[-use_first:][::-1]]
    print('MSE Array - ',mse_array)
    print('groups - ',groups)
    img = input_image.copy()
    if not shade_boxes:
        bounding_boxes = bounding_box.create_clusters(clustering_map,groups[0])
        for box in bounding_boxes:
            img = cv2.rectangle(img, (max(box[0]-2,0),max(box[1]-2,0)), (min(box[2]+2,img.shape[1]-1),min(box[3]+2,img.shape[0]+2)), (0,0,255),1)
    else:
        x = len(groups[0])
        box_colors = [(0,0,255)] if x == 1 else [(255-i*255//(x-1),0,i*255//(x-1)) for i in range(x)]
        for i,group in enumerate(groups[0]):
            bounding_boxes = bounding_box.create_clusters(clustering_map,[group])
            for box in bounding_boxes:
                img = cv2.rectangle(img, (max(box[0]-2,0),max(box[1]-2,0)), (min(box[2]+2,img.shape[1]-1),min(box[3]+2,img.shape[0]+2)), box_colors[i],1)

    cv2.imwrite(global_variables.output_dir + '/MARKED_DEFECTS'+'.png', img)

    for group in groups:
        transparent_input_image = cv2.merge((b_channel, g_channel, r_channel, alpha_channel))
        result = draw_combination_on_transparent_input_image(mse_array, clustering, group, transparent_input_image)
        cv2.imwrite(global_variables.output_dir + '/ACCEPTED_CLASSES'+'.png', result)

    print("--- PCA-Kmeans + Post-processing time - %s seconds ---" % (time.time() - start_time))

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Parameters for Running')
    parser.add_argument('-output_dir',
                        dest='output_dir',
                        help='destination directory for the output')
    parser.add_argument('-input_path',
                        dest='input_path',
                        help='path to the input image')
    parser.add_argument('-reference_path',
                        dest='reference_path',
                        help='path to the reference image')
    parser.add_argument('-n',
                        dest='n',
                        help='number of classes for clustering the diff descriptors')
    parser.add_argument('-use_first',
                        dest='use_first',
                        default = -1, help='number of classes with the highest mse scores to be slassified as defective')
    parser.add_argument('-window_size',
                        dest='window_size',
                        help='window size for the diff descriptors')
    parser.add_argument('-pca_dim_rgb',
                        dest='pca_dim_rgb',
                        help='pca target dimension for the rgb diff descriptor')
    parser.add_argument('-pca_dim_hsv',
                        dest='pca_dim_hsv',
                        help='pca target dimension for the hsv diff descriptor')
    parser.add_argument('-cut',
                        dest='cut',
                        help='true to enable DXTR cropping',
                        default=False, action='store_true')
    parser.add_argument('-lighting_fix',
                        dest='lighting_fix',
                        help='true to enable histogram matching',
                        default=False, action='store_true')
    parser.add_argument('-use_homography',
                        dest='use_homography',
                        help='true to enable SIFT homography (always recommended)',
                        default=False, action='store_true')
    parser.add_argument('-resize_factor',
                        dest='resize_factor',
                        help='scale the input images, usually with factor smaller than 1 for faster results')
    parser.add_argument('-save_extra_stuff',
                        dest='save_extra_stuff',
                        help='save diagnostics and extra results, usually for debugging',
                        default=False, action='store_true')
    parser.add_argument('-shade_boxes',
                        dest='shade_boxes',
                        help='true to colour boxes of different classes with different colors',
                        default=False, action='store_true')
    args = parser.parse_args()
    main(args.output_dir, args.input_path, args.reference_path, int(args.n),  int(args.use_first), int(args.window_size),
         int(args.pca_dim_rgb), int(args.pca_dim_hsv), bool(args.cut), bool(args.lighting_fix), bool(args.use_homography),
         float(args.resize_factor), bool(args.save_extra_stuff), bool(args.shade_boxes))