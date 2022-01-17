import numpy as np
import itertools

def around(i,j,i1,j1):
  return (i-i1)*(i-i1)+(j-j1)*(j-j1) <= 2

def intersection(box1,box2):
  xmin = max(box1[0],box2[0])
  xmax = min(box1[2],box2[2])
  ymin = max(box1[1],box2[1])
  ymax = min(box1[3],box2[3])
  if xmax<=xmin or ymax<=ymin:
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

def create_clusters(clusters, classes):
  x = clusters.copy()
  disjoint_sets = []
  binary_clusters = np.zeros_like(x)
  for i in range(x.shape[0]):
    for j in range(x.shape[1]):
      binary_clusters[i][j] = int(x[i][j] in classes)
  
  for i in range(binary_clusters.shape[0]):
    for j in range(binary_clusters.shape[1]):
      if binary_clusters[i][j] == 1:
        intersection_set = []
        for a0 in range(len(disjoint_sets)):
          disjoint_set = disjoint_sets[a0]
          for point in disjoint_set:
            if around(point[0],point[1],i,j):
              intersection_set += [a0]
              break
        if len(intersection_set)==0:
          disjoint_sets += [[[i,j]]]
        elif len(intersection_set)==1:
          disjoint_sets[intersection_set[0]] += [[i,j]]
        else:
          new_set = []
          for a0 in intersection_set:
            new_set += disjoint_sets[a0]
          disjoint_sets = [disjoint_sets[k] for k in range(len(disjoint_sets)) if k not in intersection_set]
          disjoint_sets.append(new_set)
  bboxes = []
  for i in range(len(disjoint_sets)):
    xmin, xmax, ymin, ymax = 10**6,0,10**6,0
    for point in disjoint_sets[i]:
      y, x = point[0], point[1]
      if x<xmin:
        xmin = x
      if x>xmax:
        xmax = x
      if y<ymin:
        ymin = y
      if y>ymax:
        ymax = y
    bboxes += [[xmin, ymin, xmax, ymax]]
  return reduce(bboxes)