tInt = 30
for i in range(int(1440/tInt)):
	open('./mbmData/minbymin' + str(i) + 
					  '.txt', 'a').close()

with open('mbmDec.txt') as in_file:
	brace_counter = 0
	key_counter = -1
	output = False
	s = in_file.read(1)
	if s != '{':
		print "Error at beginning"
		raise Exception()	
	while True:
		c = in_file.read(1)
		if not c or brace_counter == -1:
			with open('./mbmData/minbymin' + str(key_counter/tInt) + 
					  '.txt', 'w') as out_file:
				out_file.write(s)
				out_file.close()
			print "End of File"
			in_file.close()
			break
		s += c
		if c =='{':
			brace_counter += 1
		elif c =='}':
			brace_counter -= 1
			if brace_counter == 0 :
				key_counter += 1
				output = False
		if ((key_counter + 1) % tInt == 0 and key_counter != -1 and s[-2:] == ', ' 
			and output == False):
			print 
			s = s[:-2]
			s += '}'
			print key_counter
			print './mbmData/minbymin' + str((key_counter/tInt) - 1) + '.txt'
			with open('./mbmData/minbymin' + str(key_counter/tInt) + 
					  '.txt', 'w') as out_file:
				out_file.write(s)
				out_file.close()
			output = True
			s = '{'

