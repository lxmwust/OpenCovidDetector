from torch.utils.data import Dataset
from PIL import Image
#import torchvision.transforms.functional as functional
import torchvision.transforms as transforms
#import torchvision
import torch
from .statefultransforms import StatefulRandomCrop, StatefulRandomHorizontalFlip
import SimpleITK as sitk
import os
import glob
import numpy as np
import random
import cv2 as cv

class NCPDataset(Dataset):
    def __init__(self, data_root,index_root, padding, augment=False, pinyins=None, **kwargs):
        self.padding = padding
        self.data = []
        self.data_root = data_root
        self.padding = padding
        self.augment = augment

        with open(index_root, 'r') as f:
        #list=os.listdir(data_root)
            self.data=f.readlines()

        #for item in list:
         #   self.data.append(item)

        #print('index file:', index_root)
        print('num of data:', len(self.data))

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        #load video into a tensor
        data_path = self.data[idx]
        if data_path[-1]=='\n':
            data_path=data_path[:-1]
        cls=1-int(data_path.split('/')[-1][0]=='c')
        volume=sitk.ReadImage(os.path.join(self.data_root, data_path))
        data=sitk.GetArrayFromImage(volume)
        #data=np.stack([data,data,data],0)
        data[data>400]=400
        data[data<-1700]=-1700
        data=data+1700
        data=(data/data.max()*255).astype(np.uint8)
        #cv.imwrite('temp.jpg', data[:,64,:,:])
        temporalvolume,length = self.bbc(data, self.padding, self.augment)
        return {'temporalvolume': temporalvolume,
            'label': torch.LongTensor([cls]),
            'length':torch.LongTensor([length])
            }

    def bbc(self,V, padding, augmentation=True):
        temporalvolume = torch.zeros((3, padding, 224, 224))
        stride=V.shape[1]//padding
        croptransform = transforms.CenterCrop((224, 224))
        if (augmentation):
            crop = StatefulRandomCrop((224, 224), (224, 224))
            flip = StatefulRandomHorizontalFlip(0.5)

            croptransform = transforms.Compose([
                crop,
                flip
            ])

        for cnt,i in enumerate(range(V.shape[0]-40,45,-3 )):
        #for cnt, i in enumerate(range(V.shape[0]-5,5, -3)):
            if cnt>=padding:
                break
            result = transforms.Compose([
                transforms.ToPILImage(),
                transforms.Resize((256, 256)),
                transforms.CenterCrop((256, 256)),
                croptransform,
                transforms.ToTensor(),
                transforms.Normalize([0, 0, 0], [1, 1, 1]),
            ])(V[i-1:i+2,:,:])

            temporalvolume[:, cnt] = result
        '''
        for i in range(len(vidframes), padding):
            temporalvolume[0][i] = temporalvolume[0][len(vidframes)-1]
        '''

        if cnt==0:
            print(cnt)
        return temporalvolume,cnt

class NCP2DDataset(Dataset):
    def __init__(self, data_root,index_root, padding, augment=False):
        self.padding = padding
        self.data = []
        self.data_root = data_root
        self.padding = padding
        self.augment = augment

        with open(index_root, 'r') as f:
        #list=os.listdir(data_root)
            self.data=f.readlines()

        #for item in list:
         #   self.data.append(item)

        #print('index file:', index_root)
        print('num of data:', len(self.data))

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        #load video into a tensor
        data_path = self.data[idx]
        if data_path[-1]=='\n':
            data_path=data_path[:-1]
        cls=1-int(data_path.split('/')[-1][0]=='c')
        data=np.load(os.path.join(self.data_root, data_path))

        #data[data>400]=400
        #data[data<-1700]=-1700
        #data=data+1700
        #data=(data/data.max()*255).astype(np.uint8)
        #cv.imwrite('temp.jpg', data[:,64,:,:])
        temporalvolume,length = self.bbc(data, self.padding, self.augment)
        return {'temporalvolume': temporalvolume,
            'label': torch.LongTensor([cls]),
            'length':torch.LongTensor([length])
            }

    def bbc(self,V, padding, augmentation=True):
        temporalvolume = torch.zeros((3, padding, 224, 224))
        croptransform = transforms.CenterCrop((224, 224))
        if (augmentation):
            crop = StatefulRandomCrop((224, 224), (224, 224))
            flip = StatefulRandomHorizontalFlip(0.5)

            croptransform = transforms.Compose([
                crop,
                flip
            ])

        for cnt,i in enumerate(range(V.shape[0])):
            if cnt>=padding:
                break
            result = transforms.Compose([
                transforms.ToPILImage(),
                transforms.Resize((256, 256)),
                transforms.CenterCrop((256, 256)),
                croptransform,
                transforms.ToTensor(),
                transforms.Normalize([0, 0, 0], [1, 1, 1]),
            ])(V[i,:,:,:])

            temporalvolume[:, cnt] = result

        if cnt==0:
            print(cnt)
        return temporalvolume,cnt

class NCPJPGDataset(Dataset):
    def __init__(self, data_root,index_root, padding, augment=False,cls_num=2):
        self.padding = padding
        self.data = []
        self.data_root = open(data_root,'r').readlines()
        self.text_book=[item.split('\t') for item in self.data_root]
        self.padding = padding
        self.augment = augment
        self.cls_num=cls_num
        self.train_augmentation = transforms.Compose([transforms.Resize(256),##just for abnormal detector
                                                 transforms.RandomCrop(224),
                                                 transforms.RandomRotation(45),
                                                 #transforms.RandomAffine(45, translate=(0,0.2),fillcolor=0),

                                                 transforms.ToTensor(),
                                                 transforms.RandomErasing(p=0.1),
                                                 transforms.Normalize([0, 0, 0], [1, 1, 1])
                                                 ])
        self.test_augmentation = transforms.Compose([transforms.Resize(256),
                                                 transforms.CenterCrop(224),
                                                 transforms.ToTensor(),
                                                 transforms.Normalize([0, 0, 0], [1, 1, 1])
                                                 ])
        with open(index_root, 'r') as f:
        #list=os.listdir(data_root)
            self.data=f.readlines()

        #for item in list:
         #   self.data.append(item)

        #print('index file:', index_root)
        print('num of data:', len(self.data))
        pa_id=list(set([st.split('/')[-1].split('_')[0] for st in self.data]))
        #pa_id_0=[id[0]=='c' or id[1]=='.' for id in pa_id]
        #print(np.sum(pa_id_0),len(pa_id)-np.sum(pa_id_0))
        if self.cls_num==2:
            cls = [1 - int(data_path.split('/')[-1][0] == 'c' or data_path.split('/')[-1][1]=='.' or
                           data_path.split('/')[-2]=='masked_ild') for data_path in self.data]
        elif self.cls_num==4:
            cls=[]
            for data_path in self.data:
                if data_path.split('/')[-1][0] == 'c':
                    cls.append(0)
                elif data_path.split('/')[-1][1]=='.':
                    cls.append(1)
                elif data_path.split('/')[-2]=='masked_ild':
                    cls.append(2)
                else:
                    cls.append(3)#covid
        nums=[np.sum(np.array(cls)==i) for i in range(max(cls)+1)]
        print(nums)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        #load video into a tensor
        data_path = self.data[idx]
        if data_path[-1]=='\n':
            data_path=data_path[:-1]
        if self.cls_num==2:
            cls=1-int(data_path.split('/')[-1][0]=='c' or data_path.split('/')[-1][1]=='.' or
                      data_path.split('/')[-2]=='masked_ild')
        elif self.cls_num==3:
            if data_path.split('/')[-1][0] == 'c':
                cls = 0
            elif data_path.split('/')[-1][1] == '.' or data_path.split('/')[-2] == 'masked_ild':
                cls = 1
            else:
                cls = 2  # covid
        else:
            if data_path.split('/')[-1][0] == 'c':
                cls = 0
            elif data_path.split('/')[-1][1] == '.':
                cls = 1
            elif  data_path.split('/')[-2] == 'masked_ild':

                cls = 2  # covid
            else:
                cls=3
        data=Image.open(data_path)
        age = -1
        gender = -1
        if  data_path.split('/')[-3] == 'ILD' or \
                data_path.split('/')[-3] == 'LIDC' or \
                data_path.split('/')[-3] == 'reader_ex':
            age = -1
            gender = -1
        else:
            if data_path.split('/')[-3]=='slice_test_seg':
                if len(data_path.split('/')[-1].split('_')[1])>2:
                    a=data_path.split('/')[-1].split('c--')[-1]
                    temp='test1/'+a.split('_')[0]+'_'+a.split('_')[1]
                else:
                    a = data_path.split('/')[-1].split('c--')[-1]
                    temp='train1/'+a.split('_')[0]+'_'+a.split('_')[1]
            else:
                temp = data_path.split('/')[-2].split('_')[-1] + '/' + data_path.split('/')[-1].split('_')[0] + '_' + \
                       data_path.split('/')[-1].split('_')[1]
            for line in self.text_book:
                if line[0].split('.nii')[0] == temp:
                    age = int(line[1])
                    gender = int(line[2][:-1] == 'M')  # m 1, f 0
                    break
        if self.augment:
            data=self.train_augmentation(data)
        else:
            data=self.test_augmentation(data)
        return {'temporalvolume': data,
            'label': torch.LongTensor([cls]),
            'length':torch.LongTensor([1]),
            'gender':torch.LongTensor([gender]),
            'age':torch.LongTensor([age])
            }

class NCPJPGtestDataset(Dataset):
    def __init__(self, data_root, pre_lung_root,padding,lists=None,exlude_lists=True,age_list=None,cls_num=2):
        self.padding = padding
        self.cls_num=cls_num
        self.data = []
        self.text_book=None
        if isinstance(age_list,str):
            self.data_root = open(age_list, 'r').readlines()
            self.text_book = [item.split('\t') for item in self.data_root]
        self.mask=[]
        if isinstance(lists,list):
            if  not exlude_lists:
                self.data=lists
                self.mask=[item.split('_data')[0]+'_seg'+item.split('_data')[1][:-1] for item in self.data]
                self.data = [item[:-1] for item in self.data]
            else:
                if isinstance(data_root, list):
                    for r1, r2 in zip(data_root, pre_lung_root):
                        D= glob.glob(r1 + '/*.n*')
                        D=[t for t in D if not (t+'\n') in lists]
                        M= [item.split('_data')[0]+'_seg'+item.split('_data')[1] for item in D]
                        self.data+=D
                        self.mask+=M
                else:
                    D = glob.glob(data_root + '/*.n*')
                    D = [t for t in D if not (t+'\n') in lists]
                    M = [item.split('_data')[0] + '_seg' + item.split('_data')[1] for item in D]
                    self.data += D
                    self.mask += M
        else:

            if isinstance (data_root,list):
                for r1,r2 in zip(data_root,pre_lung_root):
                    self.data+=glob.glob(r1+'/*.n*')
                    self.mask+=glob.glob(r2+'/*.n*')
            else:
                self.data = glob.glob(data_root)
                self.mask=glob.glob(pre_lung_root)
        self.pre_root=pre_lung_root
        self.data_root = data_root
        self.padding = padding

        self.transform=  transforms.Compose([#transforms.ToPILImage(),
                                        transforms.Resize(256),
                                         transforms.CenterCrop(224),
                                         transforms.ToTensor(),
                                         transforms.Normalize([0, 0, 0], [1, 1, 1])
                                         ])
        print('num of data:', len(self.data))

        if self.cls_num == 2:
            cls = [1 - int(data_path.split('/')[-1][0] == 'c' or data_path.split('/')[-1][1] == '.' or
                           data_path.split('/')[-3] == 'ILD') for data_path in self.data]
        elif self.cls_num == 4:
            cls = []
            for data_path in self.data:
                if data_path.split('/')[-1][0] == 'c':
                    cls.append(0)
                elif data_path.split('/')[-1][1] == '.':
                    cls.append(1)
                elif data_path.split('/')[-3] == 'ILD':
                    cls.append(2)
                else:
                    cls.append(3)  # covid
        #cls=0
        nums = [np.sum(np.array(cls) == i) for i in range(max(cls) + 1)]
        print(nums)


    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        #load video into a tensor
        data_path = self.data[idx]
        mask_path=self.mask[idx]
        if data_path[-1]=='\n':
            data_path=data_path[:-1]
        if self.cls_num == 2:
            cls = 1 - int(data_path.split('/')[-1][0] == 'c' or data_path.split('/')[-1][1] == '.' or
                          data_path.split('/')[-3] == 'ILD')
        elif self.cls_num == 3:
            if data_path.split('/')[-1][0] == 'c':
                cls = 0
            elif data_path.split('/')[-1][1] == '.' or data_path.split('/')[-3] == 'ILD':
                cls = 1
            else:
                cls = 2  # covid
        else:
            if data_path.split('/')[-1][0] == 'c':
                cls = 0
            elif data_path.split('/')[-1][1] == '.':
                cls = 1
            elif data_path.split('/')[-3] == 'ILD':
                cls = 2  # covid
            else:
                cls = 3

        #cls=0
        #cls=0
        #volume = sitk.ReadImage(os.path.join(input_path, name))
        mask = sitk.ReadImage(mask_path)
        M = sitk.GetArrayFromImage(mask)
        volume=sitk.ReadImage(data_path)
        data=sitk.GetArrayFromImage(volume)
        data = data[-300:-40, :, :]
        M = M[-300:-40, :data.shape[1], :data.shape[2]]
        data=data[:M.shape[0],:M.shape[1],:M.shape[2]]
        temporalvolume,name = self.bbc(data, self.padding,M)
        age = -1
        gender = -1
        if isinstance(self.text_book,list):
            if data_path.split('/')[-3]=='ILD' or\
                  data_path.split('/')[-3] == 'LIDC' or\
                  data_path.split('/')[-3] == 'reader_ex':
                age = -1
                gender = -1

            else:
                temp = data_path.split('/')[-2].split('_')[-1] + '/' + data_path.split('/')[-1].split('_')[0] + '_' + \
                       data_path.split('/')[-1].split('_')[1]
                for line in self.text_book:
                    if line[0] == temp:
                        age = int(line[1])
                        gender = int(line[2][:-1] == 'M')  # m 1, f 0
                        break

        return {'temporalvolume': temporalvolume,
            'label': torch.LongTensor([cls]),
            'length':[data_path,name],
            'gender': torch.LongTensor([gender]),
            'age': torch.LongTensor([age])

            }

    def bbc(self,V, padding,pre=None):
        temporalvolume = torch.zeros((3, padding, 224, 224))
        #croptransform = transforms.CenterCrop((224, 224))
        cnt=0
        name=[]
        for cnt,i in enumerate(range(V.shape[0]-40,45,-5 )):
        #for cnt, i in enumerate(range(V.shape[0]-5,5, -3)):
            if cnt>=padding:
                break
            data=V[i-1:i+1,:,:]
            data[data > 700] = 700
            data[data < -1200] = -1200
            data = data * 255.0 / 1900
            name.append(i)
            data = data - data.min()
            data = np.concatenate([pre[i:i + 1, :, :] * 255,data], 0)  # mask one channel
            data = data.astype(np.uint8)
            data=Image.fromarray(data.transpose(1,2,0))
            #data.save('temp.jpg')
            result = self.transform(data)

            temporalvolume[:, cnt] = result

        if cnt==0:
            print(cnt)
        return temporalvolume,name

class NCPJPGtestDataset_MHA(Dataset):
    def __init__(self, data_root, pre_lung_root,padding,lists=None,exlude_lists=True):
        self.padding = padding
        self.data = []
        self.mask=[]
        if isinstance(lists,list):
            if  not exlude_lists:
                self.data=lists
                self.mask=[item.split('images')[0]+'lungsegs'+item.split('images')[1][:-1] for item in self.data]
                self.data = [item[:-1] for item in self.data]
            else:
                if isinstance(data_root, list):
                    for r1, r2 in zip(data_root, pre_lung_root):
                        D= glob.glob(r1 + '/*/*.mha')
                        D=[t for t in D if not (t+'\n') in lists]
                        M= [item.split('images')[0]+'lungsegs'+item.split('images')[1] for item in D]
                        self.data+=D
                        self.mask+=M
                else:
                    D = glob.glob(data_root + '/*/*.mha')
                    D = [t for t in D if not (t+'\n') in lists]
                    M = [item.split('images')[0] + 'lungsegs' + item.split('images')[1] for item in D]
                    self.data += D
                    self.mask += M
        else:
            if isinstance (data_root,list):
                for r1,r2 in zip(data_root,pre_lung_root):
                    self.data+=glob.glob(r1+'/*/*.mha')
                    self.mask+=glob.glob(r2+'/*/*.mha')
            else:
                self.data = glob.glob(data_root)
                self.mask=glob.glob(pre_lung_root)
        self.data=list(set(self.data))
        self.mask = list(set(self.mask))
        self.pre_root=pre_lung_root
        self.data_root = data_root
        self.padding = padding

        self.transform=  transforms.Compose([#transforms.ToPILImage(),
                                        transforms.Resize(256),
                                         transforms.CenterCrop(224),
                                         transforms.ToTensor(),
                                         transforms.Normalize([0, 0, 0], [1, 1, 1])
                                         ])
        print('num of data:', len(self.data))

        cls = [1 - int(data_path.split('/')[-1][0] == 'c' or data_path.split('/')[-1][1] == '.'
                       or data_path.split('/')[-3]=='ILD' or data_path.split('/')[-3]=='reader_ex') for
               data_path in self.data]
        #cls=0
        print(np.sum(np.array(cls) == 0), np.sum(np.array(cls) == 1))


    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        #load video into a tensor
        data_path = self.data[idx]
        mask_path=self.mask[idx]
        if data_path[-1]=='\n':
            data_path=data_path[:-1]
        cls=1-int(data_path.split('/')[-1][0]=='c'or
                  data_path.split('/')[-3]=='ILD' or
                  data_path.split('/')[-3] == 'LIDC' or
                  data_path.split('/')[-3] == 'reader_ex')

        #cls=0
        #cls=0
        #volume = sitk.ReadImage(os.path.join(input_path, name))
        mask = sitk.ReadImage(mask_path)
        M = sitk.GetArrayFromImage(mask)
        volume=sitk.ReadImage(data_path)
        data=sitk.GetArrayFromImage(volume)
        #data = data[-300:-40, :, :]
        #print(M.shape)
        M = M[:, :data.shape[1], :data.shape[2]]
        data=data[:M.shape[0],:M.shape[1],:M.shape[2]]
        temporalvolume,name = self.bbc(data, self.padding,M)
        return {'temporalvolume': temporalvolume,
            'label': torch.LongTensor([cls]),
            'length':[data_path,name]
            }

    def bbc(self,V, padding,pre=None):
        temporalvolume = torch.zeros((3, padding, 224, 224))
        #croptransform = transforms.CenterCrop((224, 224))
        cnt=0
        name=[]
        for cnt,i in enumerate(range(V.shape[0]-1)):
        #for cnt, i in enumerate(range(V.shape[0]-5,5, -3)):
            #if cnt>=padding:
            #    break
            data=V[i:i+1,:,:]
            data[data > 700] = 700
            data[data < -1200] = -1200
            data = data * 255.0 / 1900
            name.append(i)
            data = data - data.min()
            data = np.concatenate([pre[i:i + 1, :, :] * 255,data,data], 0)  # mask one channel
            data = data.astype(np.uint8)
            data=Image.fromarray(data.transpose(1,2,0))
            #data.save('temp.jpg')
            result = self.transform(data)

            temporalvolume[:, cnt] = result

        #if cnt==0:
        print(cnt)
        temporalvolume=temporalvolume[:,:cnt+1]
        return temporalvolume,name