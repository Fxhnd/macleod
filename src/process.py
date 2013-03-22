import os, signal, time, subprocess, process
from multiprocessing import Queue

def startSubprocess(command):
	"""Start a new subprocess, but does not wait for the subprocess to complete. 
	This method uses the os.setsid in Linux, which is not available in Windows"""
	print("---")
	print("STARTING: " + command)
	if os.name == 'nt':
		# Windows
		p = subprocess.Popen(command, shell=True, close_fds=True)
	else:
		# Linux (and others)
		p = subprocess.Popen(command, shell=True, close_fds=True, preexec_fn=os.setsid)
	
	return p


def startInteractiveProcess():
	"""Start a process whose output (STDOUT) is written to the return value."""
	if os.name == 'nt':
		# Windows
		p = subprocess.Popen(command, shell=True, close_fds=True, 
								stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	else:
		# Linux (and others)
		p = subprocess.Popen(command, shell=True, close_fds=True, preexec_fn=os.setsid, 
								stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	return p
	
			



def executeSubprocess(command, results = None):
	"""start a new subprocess and wait for it to terminate"""
	p = process.startSubprocess(command)
	p.wait()
	#print str(p.returncode) + '\n'
	if p.returncode==0:
		# give a bit of time to finish the command line output
		time.sleep(0.1)
		print("FINISHED: " + command)
		print("---")
		if results:
			results.put((command, p.returncode))
			return
		else:
			return p

		

def terminateSubprocess (process):
	"""terminate a sub process; needed for downwards compatibility with Python 2.5"""
	def terminate_win (process):
		os.system("taskkill /F /T /PID " + str(process.pid))
		#value = win32process.TerminateProcess(process._handle, -1)
#		import win32api
#		PROCESS_TERMINATE = 1
#		handle = win32api.OpenProcess(PROCESS_TERMINATE, False, process.pid)
#		win32api.TerminateProcess(handle, -1)
#		win32api.CloseHandle(handle)
		time.sleep(1.0)
		return value

	def terminate_nix (process):
		#os.kill(process.pid, signal.SIGINT)
		value = os.killpg(process.pid, signal.SIGINT)
		time.sleep(1.0)
		return value

		#return os.waitpid(process.pid, os.WNOHANG)

	terminate_default = terminate_nix
	
	handlers = {
		"nt": terminate_win, 
		"linux": terminate_nix
	}

	return handlers.get(os.name, terminate_default)(process)

#def run(command):
#	print command + ' is active'
#		process.startSubprocess(prover)
#		process.wait()
#		print command + ' returned with code ' + process.returncode
#		return process.returncode


def raceProcesses (provers, modelfinders):
	"""run a set of theorem provers and a set of model finders in parallel.
	If one terminates successfully, all others are immediately terminated.
	
	Keyword arguments:
	provers -- dictionary of theorem provers to execute where the key is the command and the value a set of return codes that indicate success.
	modelfinders -- dictionary of modelfinders to execute where the key is the command and the value a set of return codes that indicate success.
	"""
	time.sleep(0.1)
	
	#print provers
	#print modelfinders
	
	proverProcesses = []
	
	# dictionary that give each process a number as name to not have to rely on the command that is altered through serialization
	#proverDict = {}
	#i = 1
	
	import multiprocessing
	
	results = Queue()
	
	# start all processess
	for prover in (provers.keys() + modelfinders.keys()):
		#print 'Creating subprocess for ' + prover
		#proverDict[i] = prover
		# TODO: need a separate class for the execute method in order to gracefully shut it down
		p = multiprocessing.Process(name=prover.split(' ')[0], target=executeSubprocess, args=(prover,results,))
		p.start()
		time.sleep(0.1)
		proverProcesses.append(p)
		#i += 1
	
	num_running = len(proverProcesses)
	success = False
	
	time.sleep(0.1)
	#active=multiprocessing.active_children()
	while num_running>0:	
		while results.empty():
			time.sleep(1.0)
			#active=multiprocessing.active_children()	# poll for active processes
		# at least one process has terminated
		while not results.empty():
			num_running += - 1
			(name, code) = results.get()
			#name = proverDict[name]		# mapping the number back to the real command name
			#print str(name) + " returned with " + str(code)
			if name in provers:
				#print name + " finished; positive returncodes are " + str(provers[name])
				if code in provers[name]:
					print name + " found an inconsistency"
					success = True
				provers[name] = code
			if name in modelfinders:
				#print name + " finished; positive returncodes are " + str(modelfinders[name])
				if code in modelfinders[name]:
					print name + " found a model"
					success = True
				modelfinders[name] = code

		if success:
			# terminate all processes that are still active
			for p in multiprocessing.active_children():
#				print "Child process state: %d" % p.is_alive()
# TODO: want to gracefully shut down				
#				p.terminate()
				time.sleep(1.0)
#    			if p.is_alive():
#	       			print "Child process state: %d" % p.is_alive()
#       			os.kill(p.pid, signal.SIGTERM)
#       			time.sleep(1.0)
#       			if p.is_alive():
#       				os.kill(p.pid, signal.SIGKILL)
#       				time.sleep(1.0)
       			os.system("taskkill /F /T /PID " + str(p.pid))
		       			#os.system("taskkill /im /f")
#       			import win32api
#       			PROCESS_TERMINATE = 1
#       			handle = win32api.OpenProcess(PROCESS_TERMINATE, False, p.pid())
#       			win32api.TerminateProcess(handle, -1)
#       			win32api.CloseHandle(handle)
		break


	return (provers, modelfinders)

		#num_running = len(active)
#		print(str(num_running) + " active processses")
#		time.sleep(0.5)
#		for p in proverProcesses:
#			if p not in active:
#				print p
#				if p.returncode in p.provers[p.name()]:
#					success = True
#		for p in finderProcesses:
#			if p not in active:
#				print p
#				if p.returncode in p.finders[p.name()]:
#					success = True

#	for prover in proverProcesses:
#		provers[prover.name()]=prover.returncode
#	for finder in finderProcesses:
#		modelfinders[finder.name()]=find.returncode