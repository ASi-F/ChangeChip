import numpy as np
import itertools

def max_coords(i,j,clusters,classes):
  if i >= clusters.shape[0]-1:
    if j >= clusters.shape[1]-1:
      return i,j
  
  if i >= clusters.shape[0]-1:
    if clusters[i][j+1] not in classes:
      return i,j
    else:
      return max_coords(i,j+1,clusters,classes)
  
  if j >= clusters.shape[1]-1:
    if clusters[i+1][j] not in classes:
      return i,j
    else:
      return max_coords(i+1,j,clusters,classes)

  if clusters[i+1][j] not in classes:
    if clusters[i+1][j+1] not in classes:
      if clusters[i][j+1] not in classes:
        return i,j
  
  y1,x1= max_coords(i+1,j+1,clusters,classes)
  y2,x2 = max_coords(i+1,j+1,clusters,classes)
  y3,x3 = max_coords(i,j+1,clusters,classes)

  return max(y1,y2,y3),max(x1,x2,x3)

def intersection(box1,box2):
  xmin = max(box1[0],box2[0])
  xmax = min(box1[2],box2[2])
  ymin = max(box1[1],box2[1])
  ymax = min(box1[3],box2[3])
  if xmin<=xmax and ymin<=ymax:
    return True
  else:
    return False

def union(boxes, intersection_set):

  xmin = min([boxes[i][0] for i in intersection_set])
  xmax = max([boxes[i][2] for i in intersection_set])
  ymin = min([boxes[i][1] for i in intersection_set])
  ymax = max([boxes[i][3] for i in intersection_set])
  return [xmin,ymin,xmax,ymax]

def reduce(boxes):
  new = []
  intersection_sets = []
  for i in range(len(boxes)):
    for j in range(i+1,len(boxes)):
      if intersection(boxes[i],boxes[j]):
        flag = False
        for k in range(len(intersection_sets)):
          if i in intersection_sets[k] or j in intersection_sets[k]:
            flag = True
            intersection_sets[k] = list(set(intersection_sets[k]+[i,j]))
            break
        if not flag:
          intersection_sets += [[i,j]]
  all_intersections = list(set(itertools.chain.from_iterable(intersection_sets))) 
  new = [boxes[i] for i in range(len(boxes)) if i not in all_intersections]
  for i in range(len(intersection_sets)):
    new += [union(boxes,intersection_sets[i])]
  return new

def bboxes(clusters, classes, thresh):
  masks = clusters.copy()
  boxes = []
  for i in range(clusters.shape[0]):
    for j in range(clusters.shape[1]):
      if masks[i][j] != -1:
        if clusters[i][j] in classes :
          ymin = i
          xmin = j
          ymax, xmax = max_coords(i,j,clusters,classes)
          if (xmax-xmin)*(ymax-ymin) >= thresh:
            boxes.append([xmin,ymin,xmax,ymax])
          for a0 in range(xmin,xmax+1):
            for b0 in range(ymin,ymax+1):
              masks[b0][a0] = -1
        else:
          masks[i][j] = -1

  return reduce(boxes)