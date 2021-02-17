import numpy as np
import matplotlib.patches as patch
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import scipy.signal as signal
import glob
import copy
import sys
import os
import math
import json
import cv2
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from joblib import dump, load
import pandas as pd
import warnings
os.chdir('/Users/annzhou/research/neuroscience/ChenLab_Sleep_Scoring/')
import SWS_utils
from SW_Cursor import Cursor

key_stroke = 0

def on_press(event):
	global key_stroke
	if event.key in ['1','2','3']:
		key_stroke = int(event.key)
		print(f'scored: {event.key}')
	elif event.key == 'q':
		print('QUIT')
		plt.close('all')
		sys.exit()
	else:
		key_stroke = np.float('nan')
		print('I did not understand that keystroke, I will go back to it at the end')


def load_data_for_sw(filename_sw):
    '''
     load_data_for_sw(filename_sw)
    '''
    with open(filename_sw, 'r') as f:
           d = json.load(f)

    extracted_dir = str(d['savedir'])
    epochlen = int(d['epochlen'])
    fsd = int(d['fsd'])
    emg_flag = int(d['emg'])
    vid_flag = int(d['vid'])
	model_dir = str(d['model_dir'])
	animal = str(d['animal'])
	mod_name = str(d['mod_name'])

    start_swscoring(filename_sw, extracted_dir, epochlen, fsd, emg_flag, vid_flag, animal, model_dir, mod_name)

def start_swscoring(filename_sw, extracted_dir,  epochlen, fsd, emg_flag, vid_flag, animal, model_dir, mod_name):
	# mostly for deprecated packages
	print('this code is supressing warnings')
	warnings.filterwarnings("ignore")

	with open(filename_sw, 'r') as f:
			d = json.load(f)

	acq = d['Acquisition']
	video_dir = d['video_dir']

	print('These are the available acquisitions: '+ str(acq))

	a = input('Which acqusition do you want to score?')


	print('Loading EEG and EMG....')
	downsampEEG = np.load(os.path.join(extracted_dir,'downsampEEG_Acq'+str(a)+'.npy'))
	if emg_flag:
		downsampEMG = np.load(os.path.join(extracted_dir,'downsampEMG_Acq'+str(a)+'.npy'))
	acq_len = np.size(downsampEEG)/fsd # fs: sampling rate, fsd: downsampled sampling rate
	hour_segs = math.ceil(acq_len/3600) # acq_len in seconds, convert to hours
	print('This acquisition has ' +str(hour_segs)+ ' segments.')

	for h in np.arange(hour_segs):
		this_eeg = np.load(os.path.join(extracted_dir, 'downsampEEG_Acq'+str(a) + '_hr' + str(h)+ '.npy'))
		if int(d['emg']) == 1:
			this_emg = np.load(os.path.join(extracted_dir,'downsampEMG_Acq'+str(a) + '_hr' + str(h)+ '.npy'))
		# chop off the remainder that does not fit into the 4s epoch
		seg_len = np.size(this_eeg)/fsd
		nearest_epoch = math.floor(seg_len/epochlen)
		new_length = int(nearest_epoch*epochlen*fsd)
		this_eeg = this_eeg[0:new_length]
		if vid_flag:
			this_video = glob.glob(os.path.join(video_dir, '*_'+str(int(a)-1)+'.mp4'))[0]
			print('using ' + this_video + ' for the video')
		else:
			print('no video available')

		os.chdir(extracted_dir)
		print('Generating EMG vectors...')
		if emg_flag:
			EMGamp, EMGmax, EMGmean = SWS_utils.generate_signal(this_emg, epochlen, fsd)
		else:
			EMGamp = False

		print('Generating EEG vectors...')
		EEGamp, EEGmax, EEGmean = SWS_utils.generate_signal(this_eeg, epochlen, fsd)

		print('Extracting delta bandpower...') # non RAM (slow wave) sleep value | per epoch
		EEGdelta, idx_delta = SWS_utils.bandPower(0.5, 4, this_eeg, epochlen, fsd)

		print('Extracting theta bandpower...') # awake / RAM sleep
		EEGtheta, idx_theta = SWS_utils.bandPower(4, 8, this_eeg, epochlen, fsd)

		print('Extracting alpha bandpower...') # awake / RAM; not use a lot
		EEGalpha, idx_alpha = SWS_utils.bandPower(8, 12, this_eeg, epochlen, fsd)

		print('Extracting beta bandpower...') # awake; not use a lot
		EEGbeta, idx_beta = SWS_utils.bandPower(12, 30, this_eeg, epochlen, fsd)

		print('Extracting gamma bandpower...') # only awake
		EEGgamma, idx_gamma = SWS_utils.bandPower(30, 80, this_eeg, epochlen, fsd)

		print('Extracting narrow-band theta bandpower...') # broad-band theta
		EEG_broadtheta, idx_broadtheta = SWS_utils.bandPower(2, 16, this_eeg, epochlen, fsd)

		print('Boom. Boom. FIYA POWER...')
		EEGfire, idx_fire = SWS_utils.bandPower(4, 20, this_eeg, epochlen, fsd)

		EEGnb = EEGtheta / EEG_broadtheta # narrow-band theta
		delt_thet = EEGdelta / EEGtheta # ratio; esp. important

		EEGdelta = SWS_utils.normalize(EEGdelta)
		EEGalpha = SWS_utils.normalize(EEGalpha)
		EEGbeta = SWS_utils.normalize(EEGbeta)
		EEGgamma = SWS_utils.normalize(EEGbeta)
		EEGnb = SWS_utils.normalize(EEGnb)
		EEGtheta = SWS_utils.normalize(EEGtheta)
		EEGfire = SWS_utils.normalize(EEGfire)
		delt_thet = SWS_utils.normalize(delt_thet)

		# frame shifting
		delta_post, delta_pre = SWS_utils.post_pre(EEGdelta, EEGdelta)
		theta_post, theta_pre = SWS_utils.post_pre(EEGtheta, EEGtheta)
		delta_post2, delta_pre2 = SWS_utils.post_pre(delta_post, delta_pre)
		theta_post2, theta_pre2 = SWS_utils.post_pre(theta_post, theta_pre)
		delta_post3, delta_pre3 = SWS_utils.post_pre(delta_post2, delta_pre2)
		theta_post3, theta_pre3 = SWS_utils.post_pre(theta_post2, theta_pre2)
		nb_post, nb_pre = SWS_utils.post_pre(EEGnb, EEGnb)

###--------------------------------This is where the model stuff will go--------------------###

		animal_name = np.full(np.size(delta_pre), animal)
		# Note: The second parameter depends on the actual animal name. For example, if the animal is "KNR00004", we
		# should use "animal[3:]" for "00004"; if the animal is "jaLC_FLiPAKAREEGEMG004", we should use "animal[19:]"
		# for "004".
		animal_num = np.full(np.shape(animal_name), int(animal[19:]))

		model = input('Use a random forest? y/n: ') == 'y'

		if model:
			final_features = ['Animal_Name', 'animal_num', 'Time_Interval', 'State', 'delta_pre', 'delta_pre2',
							  'delta_pre3', 'delta_post', 'delta_post2', 'delta_post3', 'EEGdelta', 'theta_pre',
							  'theta_pre2', 'theta_pre3',
							  'theta_post', 'theta_post2', 'theta_post3', 'EEGtheta', 'EEGalpha', 'EEGbeta',
							  'EEGgamma', 'EEGnarrow', 'nb_pre', 'delta/theta', 'EEGfire', 'EEGamp', 'EEGmax',
							  'EEGmean', 'EMG', 'Motion']

			# TODO: take into consideration if there is not a model initially
			# loading different models
			os.chdir(model_dir)
			if emg_flag:
				clf = load(mod_name + '_EMG.joblib')
			else:
				clf = load(mod_name + '_no_EMG.joblib')

			# feature list
			FeatureList = []
			nans = np.full(np.shape(animal_name), np.nan)
			if emg_flag:
				FeatureList = [animal_num, delta_pre, delta_pre2, delta_pre3, delta_post, delta_post2, delta_post3,
							   EEGdelta,
							   theta_pre, theta_pre2, theta_pre3, theta_post, theta_post2, theta_post3,
							   EEGtheta, EEGalpha, EEGbeta, EEGgamma, EEGnb, nb_pre, delt_thet, EEGfire, EEGamp, EEGmax,
							   EEGmean, EMGamp]
			else:
				FeatureList = [animal_num, delta_pre, delta_pre2, delta_pre3, delta_post, delta_post2, delta_post3,
							   EEGdelta,
							   theta_pre, theta_pre2, theta_pre3, theta_post, theta_post2, theta_post3,
							   EEGtheta, EEGalpha, EEGbeta, EEGgamma, EEGnb, nb_pre, delt_thet, EEGfire, EEGamp, EEGmax,
							   EEGmean, nans]

			FeatureList_smoothed = []
			for f in FeatureList:
				FeatureList_smoothed.append(signal.medfilt(f, 5))
			Features = np.column_stack((FeatureList_smoothed))
			Features = np.nan_to_num(Features)

			Predict_y = clf.predict(Features)
			Predict_y = SWS_utils.fix_states(Predict_y)
			SWS_utils.create_prediction_figure(Predict_y, clf, Features, fsd, this_eeg)



		fig, (ax1, ax2, ax3, ax4) = plt.subplots(nrows = 4, ncols = 1, figsize = (11,6))
		fig2, ax5, ax6 = SWS_utils.create_scoring_figure(extracted_dir, a, eeg=this_eeg, fsd=fsd)
		# cursor = Cursor(ax5, ax6, ax7)
		cID2 = fig.canvas.mpl_connect('key_press_event', on_press)
		cID3 = fig2.canvas.mpl_connect('key_press_event', on_press)
		i = 0
		start = int(i * fsd * epochlen)
		end = int(start + fsd * 3 * epochlen)
		realtime = np.arange(np.size(this_eeg))/fsd
		LFP_ylim = 5
		delt = np.load(os.path.join(extracted_dir,'delt' + str(a) + '_hr' + str(h)+ '.npy'))
		thet = np.load(os.path.join(extracted_dir,'thet' + str(a) + '_hr' + str(h)+ '.npy'))

		no_delt_start, = np.where(realtime<delt[1][0])
		no_delt_end, = np.where(realtime>delt[1][-1])
		delt_pad = np.pad(delt[0], (np.size(no_delt_start), np.size(no_delt_end)), 'constant', 
		    constant_values=(0,0))

		no_thet_start, = np.where(realtime<thet[1][0])
		no_thet_end, = np.where(realtime>thet[1][-1])
		thet_pad = np.pad(thet[0], (np.size(no_thet_start), np.size(no_thet_end)), 'constant', 
		    constant_values=(0,0))

		assert np.size(delt_pad) == np.size(this_eeg) == np.size(thet_pad)

		line1, line2, line3, line4 = SWS_utils.pull_up_raw_trace(ax1, ax2, ax3,ax4, 
			emg_flag, start, end, realtime, this_eeg, fsd, LFP_ylim, delt_pad, 
			thet_pad, epochlen, this_emg)
		marker = SWS_utils.make_marker(ax5, end, realtime, fsd, epochlen)
		fig.show()
		fig2.show()
		fig.tight_layout()
		fig2.tight_layout()
		try:
			# if some portion of the file has been previously scored
			State = np.load(os.path.join(extracted_dir, 'StatesAcq' + str(a) + '_hr' + str(h)+'.npy'))
			wrong, = np.where(np.isnan(State))
			State[wrong] = 0
			s, = np.where(State == 0)
			color_dict = {'0': 'white',
						'1':'green',
						'2': 'blue',
						'3': 'red'}
			# rendering what has been previously scored
			for count,color in enumerate(State[:-1]):
				start = int(count * fsd * epochlen)
				rect = patch.Rectangle((realtime[start+(epochlen*fsd)],0),
					(epochlen), 1, color = color_dict[str(int(color))])
				ax6.add_patch(rect)
			fig2.show()

		except FileNotFoundError:
			# if the file is a brand new one for scoring
			State = np.zeros(int(np.size(this_eeg)/fsd/epochlen))
			s = np.arange(1,np.size(State)-1)
			first_state = int(input('Enter the first state: '))
			State[0] = first_state

		if vid_flag:
			cap = cv2.VideoCapture(this_video)
			fps = cap.get(cv2.CAP_PROP_FPS)
		for i in s[:-3]:
			# input('press enter or quit')
			print(f'here. index: {i}')
			start = int(i * fsd * epochlen)
			end = int(start + fsd * 3 * epochlen)
			if vid_flag:
				vid_start = int(i * fps * epochlen)
				vid_end = int(vid_start + fps * 3 * epochlen)
			SWS_utils.update_raw_trace(line1, line2, line3, line4, marker, fig, fig2, start, end, 
				this_eeg, delt_pad, thet_pad, emg_flag, this_emg, realtime)
			color_dict = {'0': 'white',
						'1':'green',
						'2': 'blue',
						'3': 'red'}
			rect = patch.Rectangle((realtime[start],0),
				(epochlen), 1, color = color_dict[str(int(State[i-1]))])
			ax6.add_patch(rect)
			fig.show()
			fig2.show()
			button = False
			while not button:
				button = fig2.waitforbuttonpress()
				print('here1')
				print(f'button: {button}')
				if not button:
					print('you clicked')
					if vid_flag:
						SWS_utils.pull_up_movie(vid_start, vid_end, this_video, epochlen)
					else:
						print('...but you do not have videos available')
			global key_stroke
			State[i] = key_stroke
			fig2.canvas.flush_events()
			fig.canvas.flush_events()
			np.save(os.path.join(extracted_dir, 'StatesAcq' + str(a) + '_hr' + str(h)+'.npy'), State)
		print('DONE SCORING')
		plt.close('all')
		last_state = int(input('Enter the last state: '))
		State[-2:] = last_state
		np.save(os.path.join(extracted_dir, 'StatesAcq' + str(a) + '_hr' + str(h)+'.npy'), State)

		



















