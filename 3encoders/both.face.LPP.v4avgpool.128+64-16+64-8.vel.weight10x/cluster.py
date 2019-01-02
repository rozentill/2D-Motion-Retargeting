import numpy as np
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.metrics import silhouette_score
import matplotlib.pyplot as plt
import matplotlib.cm as cm
plt.switch_backend('agg')
import torch
from dataset import get_dataloaders
import cv2
import time


def tsne_on_pca(arr, is_PCA=True):
    """
    visualize through t-sne on pca reduced data
    :param arr: (nr_examples, nr_features)
    :return:
    """
    if is_PCA:
        pca_50 = PCA(n_components=50)
        arr = pca_50.fit_transform(arr)
    tsne_2 = TSNE(n_components=2)
    res = tsne_2.fit_transform(arr)
    return res


def cluster_body(net, cluster_data, device, save_path, is_draw=True):
    data, characters = cluster_data[0], cluster_data[2]
    data = data[:, :, ::2, :, :].transpose(1, 2)
    data = data.reshape(-1, data.shape[2], data.shape[3], data.shape[4])

    nr_mv, nr_char = data.shape[0], data.shape[1]
    labels = np.arange(0, nr_char).reshape(1, -1)
    labels = np.tile(labels, (nr_mv, 1)).reshape(-1)

    features = net.body_encoder(data.contiguous().view(-1, data.shape[2], data.shape[3])[:, :-2, :].to(device))
    features = features.detach().cpu().numpy().reshape(features.shape[0], -1)

    sil_score = silhouette_score(features, labels)

    if not is_draw:
        return sil_score, None

    features_2d = tsne_on_pca(features, is_PCA=False)
    features_2d = features_2d.reshape(nr_mv, nr_char, -1)

    plt.figure(figsize=(7, 4))
    colors = cm.rainbow(np.linspace(0, 1, nr_char))
    for i in range(nr_char):
        x = features_2d[:, i, 0]
        y = features_2d[:, i, 1]
        plt.scatter(x, y, c=colors[i], label=characters[i])

    plt.legend(bbox_to_anchor=(1.04, 1), borderaxespad=0)
    plt.tight_layout(rect=[0,0,0.75,1])
    plt.savefig(save_path)

    img = cv2.imread(save_path)

    return sil_score, img


def cluster_view(net, cluster_data, device, save_path, is_draw=True):
    data, views = cluster_data[0], cluster_data[3]
    idx = np.linspace(0, data.shape[1] - 1, 4, dtype=int).tolist()
    data = data[:, idx, :, :, :]
    data = data.reshape(-1, data.shape[2], data.shape[3], data.shape[4])

    nr_mc, nr_view = data.shape[0], data.shape[1]
    labels = np.arange(0, nr_view).reshape(1, -1)
    labels = np.tile(labels, (nr_mc, 1)).reshape(-1)

    features = net.view_encoder(data.contiguous().view(-1, data.shape[2], data.shape[3])[:, :-2, :].to(device))
    features = features.detach().cpu().numpy().reshape(features.shape[0], -1)

    sil_score = silhouette_score(features, labels)

    if not is_draw:
        return sil_score, None

    features_2d = tsne_on_pca(features, is_PCA=False)
    features_2d = features_2d.reshape(nr_mc, nr_view, -1)

    plt.figure(figsize=(7, 4))
    colors = cm.rainbow(np.linspace(0, 1, nr_view))
    for i in range(nr_view):
        x = features_2d[:, i, 0]
        y = features_2d[:, i, 1]
        plt.scatter(x, y, c=colors[i], label=views[i])

    plt.legend(bbox_to_anchor=(1.04, 1), borderaxespad=0)
    plt.tight_layout(rect=[0, 0, 0.75, 1])
    plt.savefig(save_path)

    img = cv2.imread(save_path)

    return sil_score, img


def cluster_motion(net, cluster_data, device, save_path, nr_anims=15, is_draw=True, mode='both'):
    data, animations = cluster_data[0], cluster_data[1]
    idx = np.linspace(0, data.shape[0] - 1, nr_anims, dtype=int).tolist()
    data = data[idx]
    animations = animations[idx]
    if mode == 'body':
        data = data[:, :, 3, :, :].reshape(nr_anims, -1, data.shape[3], data.shape[4])
    elif mode == 'view':
        data = data[:, 3, :, :, :].reshape(nr_anims, -1, data.shape[3], data.shape[4])
    else:
        data = data[:, :3, ::2, :, :].reshape(nr_anims, -1, data.shape[3], data.shape[4])

    nr_anims, nr_cv = data.shape[:2]
    labels = np.arange(0, nr_anims).reshape(-1, 1)
    labels = np.tile(labels, (1, nr_cv)).reshape(-1)

    features = net.mot_encoder(data.contiguous().view(-1, data.shape[2], data.shape[3]).to(device))
    features = features.detach().cpu().numpy().reshape(features.shape[0], -1)

    sil_score = silhouette_score(features, labels)

    if not is_draw:
        return sil_score, None

    features_2d = tsne_on_pca(features)
    features_2d = features_2d.reshape(nr_anims, nr_cv, -1)
    if features_2d.shape[1] < 5:
        features_2d = np.tile(features_2d, (1, 2, 1))

    plt.figure(figsize=(7, 4))
    colors = cm.rainbow(np.linspace(0, 1, nr_anims))
    for i in range(nr_anims):
        x = features_2d[i, :, 0]
        y = features_2d[i, :, 1]
        plt.scatter(x, y, c=colors[i], label=animations[i])

    plt.legend(bbox_to_anchor=(1.04, 1), borderaxespad=0)
    plt.tight_layout(rect=[0,0,0.6,1])
    plt.savefig(save_path)

    img = cv2.imread(save_path)

    return sil_score, img


def test():
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    path = '/home1/wurundi/code/fbxMotionDisentangled/2d.v1fix.aug.fbxjoints.11anim.15joints.layer64/train_log/model/epoch300.pth.tar'
    net = torch.load(path)['net']

    train_ds = get_dataloaders('train', batch_size=1)

    cluster_data = train_ds.dataset.get_cluster_data()

    since = time.time()
    score, img = cluster_view(net, cluster_data, device, './cluster_body.png')
    print('times: {}'.format(time.time() - since))
    print(score)

    since = time.time()
    score, img = cluster_motion(net, cluster_data, device, './cluster_motion.png')
    print('times: {}'.format(time.time() - since))
    print(score)


if __name__ == '__main__':
    test()