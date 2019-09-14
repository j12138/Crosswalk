
from imgaug import augmenters as iaa
import numpy as np
import cv2

#Apply various augmentations from imgaug
def blur():
    blurer=[iaa.GaussianBlur((0, 3.0)),iaa.AverageBlur(k=(2, 7)),iaa.MedianBlur(k=(3, 11))]
    return blurer[np.random.randint(0,3)]

#Dropout may not be appropriate, so its not currently used
def dropout():
    dropper=[iaa.Dropout((0.01, 0.1), per_channel=0.5), iaa.CoarseDropout((0.03, 0.15), size_percent=(0.02, 0.05), per_channel=0.2)]
    return dropper[np.random.randint(0,2)]

def noise():
    return iaa.AdditiveGaussianNoise(loc=0, scale=(0.0, 0.05*255), per_channel=0.5)

def contrast():
    return iaa.ContrastNormalization((0.5, 2.0), per_channel=0.5)

def greyscale():
    return iaa.Grayscale(alpha=(0.0, 1.0))

def invert():
    return iaa.Invert(0.05, per_channel=True)

def hue():
    return iaa.AddToHueAndSaturation((-20, 20))

def add(): 
    return iaa.Add((-10, 10), per_channel=0.5)

def multiply():
    return iaa.Multiply((0.5, 1.5), per_channel=0.5)

def sharpen(): 
    return iaa.Sharpen(alpha=(0, 1.0), lightness=(0.75, 1.5))

def emboss(): 
    return iaa.Emboss(alpha=(0, 1.0), strength=(0, 2.0))
   
def translate():
    return iaa.Affine(translate_percent={"x": (0.0, 0.0), "y": (-0.03, 0.03)},mode='edge')
    
def rotate():
    return iaa.Affine(rotate=(-3, 3),mode='edge')    

   
def augment(imgs,max_augs,affine=False,debug=False):
    """Applys a series of augmentations to an image
    # Arguments
        imgs: the input images
        max_augs: the maximum number of augmentations to apply
    # Returns
        Augmented images
    """
    augmented=[]
    for img in imgs:
        if affine:
            affine_augs=[translate(),rotate()]            
            seq_affine=iaa.Sequential(affine_augs)
            
            try:
                img=seq_affine.augment_image(img)
            except:
                print(img)
                pass
        #Choose a number of augmentations to use
        num_aug=np.random.randint(0,max_augs+1)
        #set of augmentations to use
        #add(),multiply(),
        augs=[blur(),noise(),contrast(),greyscale(),invert(),hue(),sharpen(),emboss()]
        #apply augmentations
        seq=iaa.Sequential(list(np.random.choice(augs,num_aug)))
        aug_img=seq.augment_image(img)
        
        #For Debugging of augmentations
        if debug:
            cv2.imshow('frame',aug_img)
            cv2.waitKey(1000)
        augmented.append(aug_img)
        
    return np.asarray(augmented)


    
class BatchGenerator:
    
    def __init__(self,X,y, batch_size,noaugs=False, num_aug=5,
            affine=False,height=None, width=None):
        self.X=X
        self.y=y
        self.batch_size = batch_size
        self.noaugs=noaugs
        self.num_aug=num_aug
        self.affine=affine
        self.height=height
        self.width=width
        
    def __iter__(self):
        return self

    def __next__(self):
        indecies = np.random.randint(0,self.X.shape[0],self.batch_size)
        
        if self.noaugs:
            images = self.X[indecies]/255.0
            target = self.y[indecies]

            for i in range(self.batch_size):
                target[i][1] /= 90.0
            
           # print(target[1])

            return images, target

        imgs = augment(self.X[indecies],self.num_aug,self.affine)/255.0
        
        target = self.y[indecies]
        return imgs, target
    
    
