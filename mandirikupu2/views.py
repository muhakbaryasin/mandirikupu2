from pyramid.view import view_config
from time import sleep
from .Filelogger import FileLogger
from .MandiriKupu2Controller import MandiriKupu2Controller
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.firefox.options import Options as selopt
#from selenium.webdriver.chrome.options import Options as selopt
from pyquery import PyQuery as pq
from copy import deepcopy

import logging
log = logging.getLogger(__name__)

class MainView(object):
	def __init__(self, request):
		self.request = request
		self.wd = None

	@view_config(route_name='home', renderer='templates/mytemplate.jinja2')
	def my_view(self):
		return {'project': 'mandirikupu2'}
		
	@view_config(route_name='mutasi', renderer='json')
	def mutasi(self):
		try:
			reqon = MandiriKupu2Controller(self.request)
			reqon.checkComplete(reqon.REQ_MUTASI)
			
			username = self.request.params['username']
			password = self.request.params['password']
			rekening = self.request.params['rekening']
			from_date = self.request.params['from_date']
			to_date = self.request.params['to_date']
			
			from_date = datetime.strptime( from_date,'%Y-%m-%d').strftime('%d/%m/%Y')
			to_date = datetime.strptime( to_date,'%Y-%m-%d').strftime('%d/%m/%Y')
			
			return {'code' : 'OK', 'message' : '' , 'data' : {'mutasi' : self.__scraping_mutasi(username, password, rekening, from_date, to_date), 'rekening' : rekening}}
			
		except Exception as e:
			log.exception('view exception error - {}'.format(str(e)))
			return {'code' : 'ERROR', 'message' : 'error - {}'.format(str(e)) , 'data' : None}
			
	
	def __scraping_mutasi(self, user_name, password, rekening, from_date, to_date):
		try:
			#rekening = '1210060608886'
			#date1 = '14/05/2019'
			#date2 = '14/05/2019'
			#username = xxx
			#password = xxx

			#viewSearch
			#fromDate
			#toDate

			#btnReset
			#btnClose
			#btnSearch
			#options = ChrmOpt()
			options = selopt()
			options.set_headless(headless=True)
			
			self.wd = webdriver.Firefox(firefox_options=options, executable_path='geckodriver.exe')
			#self.wd = webdriver.Chrome(chrome_options=options, executable_path='chromedriver.exe')
			
			attempt = 0
			
			self.wd.get('https://ibank.bankmandiri.co.id/retail3/')
			main_frame = self.wd.find_elements_by_name('mainFrame')
			self.wd.switch_to.frame(main_frame[0])
			self.wd.find_elements_by_id('userid_sebenarnya')[0].send_keys(user_name)
			self.wd.find_elements_by_id('pwd_sebenarnya')[0].send_keys(password)
			sleep(1)
			self.wd.find_elements_by_id('btnSubmit')[0].click()
			self.wd.save_screenshot("ss/{}-login.png".format(rekening))
			
			element_rek = None
			
			while (True):
				#self.wd.save_screenshot("ss/{}-02-nunggu_rekening_clickable-attempt {}.png".format(rekening, attempt))
				
				if attempt > 60:
					break
				
				try:
					self.wd.save_screenshot("ss/{}-daftar rekening.png".format(rekening))
					element_rek[0].find_elements_by_class_name('acc-left')[0].click()
					break
				except Exception as e:
					print(str(e))
					log.info('nunggu element rekening clickable')
					attempt += 1
					sleep(1)
					element_rek = self.wd.find_elements_by_id('currentId-' + rekening)
			
			if attempt > 60:
				raise Exception('nungguin daftar mutasi rekening {} tanggal {} - {} udah lewat 60 detik masih loading'.format(rekening, from_date, to_date))
			
			element_search = None
			
			element_search = self.wd.find_elements_by_id('viewSearch')
			while ((type(element_search) is list and len(element_search) < 1)) and attempt <= 60:
				attempt += 1
				sleep(1)
				element_search = self.wd.find_elements_by_id('viewSearch')
			
			if attempt > 60:
				raise Exception('nungguin daftar mutasi rekening {} tanggal {} - {} udah lewat 60 detik masih loading'.format(rekening, from_date, to_date))
			
			element_from_date = self.wd.find_elements_by_id('fromDate')
			
			while (not element_from_date[0].is_displayed()):
				log.info('nunggu sampai from pencarian kebuka')
				self.wd.execute_script("document.getElementById('viewSearch').click()")
				attempt += 1
				sleep(1)
				element_from_date = self.wd.find_elements_by_id('fromDate')
			
			if attempt > 60:
				raise Exception('nungguin daftar mutasi rekening {} tanggal {} - {} udah lewat 60 detik masih loading'.format(rekening, from_date, to_date))
			
			#print(type(element_search))
			#print(len(element_search))
			#print(type(element_search) is list and len(element_search) < 1)
			self.wd.execute_script("$('#fromDate').val('{}')".format(from_date))
			self.wd.execute_script("$('#toDate').val('{}')".format(to_date))
			
			btn_search = self.wd.find_elements_by_id('btnSearch')
			while (True):
				if attempt > 60:
					break
				
				try:
					btn_search[0].click()
					break
				except:
					log.info('nunggu element btn search clickable')
					attempt += 1
					sleep(1)
					btn_search = self.wd.find_elements_by_id('btnSearch')
			
			if attempt > 60:
				raise Exception('nungguin daftar mutasi rekening {} tanggal {} - {} udah lewat 60 detik masih loading'.format(rekening, from_date, to_date))

			entry_mutasi = []
			table = None
			
			while (True):
				#self.wd.save_screenshot("ss/{}-04-nunggu_loading_mutasi-attempt {}.png".format(rekening, attempt))
				table = pq(self.wd.page_source)('#globalTable')
				
				if pq(pq(table)('table tbody tr.odd')[0]).text().find('Loading') > -1 and attempt <= 60:
					log.info('nunggu loading daftar transaksi')
					attempt += 1
					sleep(1)
				else: break
					
			if attempt > 60:
				raise Exception('nungguin daftar mutasi rekening {} tanggal {} - {} udah lewat 60 detik masih loading'.format(rekening, from_date, to_date))
			
			log.info('parsing daftar mutasi {} - {}'.format(from_date, to_date))
			self.wd.save_screenshot("ss/{}-daftar mutasi.png".format(rekening))
			
			if pq(table)('table tbody tr').length < 1:
				raise Exception('gak ada daftar mutasi rekening {} tanggal {} - {}'.format(rekening, from_date, to_date))

			for each_row in pq(table)('table tbody tr'):
				tiap_mutasi = {}
				tiap_mutasi['tanggal'] = pq(each_row)('.trxdate').text()
				tiap_mutasi['keterangan'] = pq(each_row)('.history-list-name').text()	
				debit_kredit = pq(each_row)('.right')	
				tiap_mutasi['debet'] = pq(debit_kredit[0]).text()
				tiap_mutasi['kredit'] = pq(debit_kredit[1]).text()
				entry_mutasi.append(deepcopy(tiap_mutasi))
			
			element_logout = None
			
			while (True):
				#self.wd.save_screenshot("ss/{}-05-nunggu_logout_clickable-attempt {}.png".format(rekening, attempt))
				
				if attempt > 60: 
					break
				
				try:
					element_logout[0].click()
					break
				except:
					log.info('nunggu logout clickable')
					attempt += 1
					sleep(1)
					element_logout = self.wd.find_elements_by_class_name('mdr-logout')
			
			if attempt > 60:
				log.warning('Gagal mencet logout - nungguin daftar mutasi rekening {} tanggal {} - {} udah lewat 60 detik masih loading'.format(rekening, from_date, to_date))
				self.wd.quit()
				return entry_mutasi
			
			element_confirm = None
			
			while (True):
				#self.wd.save_screenshot("ss/{}-06-nunggu_confim_clickable-attempt {}.png".format(rekening, attempt))
				
				if attempt > 60:
					break
				
				try:
					element_confirm[0].click()
					break
				except:
					log.info('nunggu confirm clickable')
					attempt += 1
					sleep(1)
					element_confirm = self.wd.find_elements_by_id('btnCancelReg')
			
			log.info('berhasil logout')
			self.wd.save_screenshot("ss/{}-logout.png".format(rekening))
			
			if attempt > 60:
				log.warning('Gagal mencet confirm - nungguin daftar mutasi rekening {} tanggal {} - {} udah lewat 60 detik masih loading'.format(rekening, from_date, to_date))
			
			log.info('menghapus sesi')
			self.wd.quit()
			return entry_mutasi
		except Exception as e:
			if self.wd is not None:
				
				element_logout = self.wd.find_elements_by_class_name('mdr-logout')
				while ((type(element_logout) is list and len(element_logout) < 1)) and attempt <= 60:
					attempt += 1
					sleep(1)
					element_logout = self.wd.find_elements_by_class_name('mdr-logout')
				
				if attempt > 60:
					log.warning('Gagal mencet logout - nungguin daftar mutasi rekening {} tanggal {} - {} udah lewat 60 detik masih loading'.format(rekening, from_date, to_date))
					self.wd.quit()
					raise e
				
				while (attempt <= 60):
					try:
						element_logout[0].click()
						break
					except:
						attempt += 1
						sleep(1)
						element_logout = self.wd.find_elements_by_class_name('mdr-logout')
				
				if attempt > 60:
					log.warning('Gagal mencet logout - nungguin daftar mutasi rekening {} tanggal {} - {} udah lewat 60 detik masih loading'.format(rekening, from_date, to_date))
					self.wd.quit()
					raise e
				
				
				element_confirm = self.wd.find_elements_by_id('btnCancelReg')
				
				while ((type(element_confirm) is list and len(element_confirm) < 1)) and attempt <= 60:
					attempt += 1
					sleep(1)
					element_confirm = self.wd.find_elements_by_id('btnCancelReg')
				
				if attempt > 60:
					log.warning('Gagal mencet confirm - nungguin daftar mutasi rekening {} tanggal {} - {} udah lewat 60 detik masih loading'.format(rekening, from_date, to_date))
					self.wd.quit()
					raise e
				
				while (attempt <= 60):
					try:
						element_confirm[0].click()
						break
					except:
						attempt += 1
						sleep(1)
						element_confirm = self.wd.find_elements_by_id('btnCancelReg')
				
				if attempt > 60:
					log.warning('Gagal mencet confirm - nungguin daftar mutasi rekening {} tanggal {} - {} udah lewat 60 detik masih loading'.format(rekening, from_date, to_date))
					
				self.wd.quit()
				
			raise e
