import fastai
from fastai.vision import *
from fastai.utils.mem import *
from fastai.vision import open_image, load_learner, image, torch
import streamlit as st
import numpy as np
import urllib.request
import PIL.Image
from io import BytesIO
import torchvision.transforms as T

class FeatureLoss(nn.Module):
    def __init__(self, m_feat, layer_ids, layer_wgts):
        super().__init__()
        self.m_feat = m_feat
        self.loss_features = [self.m_feat[i] for i in layer_ids]
        self.hooks = hook_outputs(self.loss_features, detach=False)
        self.wgts = layer_wgts
        self.metric_names = ['pixel',] + [f'feat_{i}' for i in range(len(layer_ids))
              ] + [f'gram_{i}' for i in range(len(layer_ids))]

    def make_features(self, x, clone=False):
        self.m_feat(x)
        return [(o.clone() if clone else o) for o in self.hooks.stored]
    
    def forward(self, input, target):
        out_feat = self.make_features(target, clone=True)
        in_feat = self.make_features(input)
        self.feat_losses = [base_loss(input,target)]
        self.feat_losses += [base_loss(f_in, f_out)*w
                             for f_in, f_out, w in zip(in_feat, out_feat, self.wgts)]
        self.feat_losses += [base_loss(gram_matrix(f_in), gram_matrix(f_out))*w**2 * 5e3
                             for f_in, f_out, w in zip(in_feat, out_feat, self.wgts)]
        self.metrics = dict(zip(self.metric_names, self.feat_losses))
        return sum(self.feat_losses)
    
    def __del__(self): self.hooks.remove()

st.write("Low Light Image Enhancement")
st.set_option('deprecation.showfileUploaderEncoding', False)

uploaded_file = st.file_uploader("Choose an image file", type=["jpg","png"])
if uploaded_file is not None:
  img = PIL.Image.open(uploaded_file).convert("RGB")
  imageLocation = st.empty()
  imageLocation.image(img, width = 512)
  MODEL_URL = "https://www.dropbox.com/s/58c3wsu9knq83b1/Goodhalf.pkl?dl=1 "
  urllib.request.urlretrieve(MODEL_URL, "Goodhalf.pkl")
  path = Path(".")
  learn=load_learner(path, 'Goodhalf.pkl')
  img_t = T.ToTensor()(img)
  img_fast = Image(img_t)
  p,img_hr,b = learn.predict(img_fast)
  img_np=image2np(img_hr)
  st.image(img_np,clamp=True,width = 512)
