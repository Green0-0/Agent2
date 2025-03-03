from agent2.file import File

file = File("test.py", """class thing:
    @param
    def test(self):
        pass
    @param1
    @param2
    def init():
        @nested
        def nestedinit():
            pass
        pass
    def noparams():
        def nested():
            pass
        pass""")
print(file.updated_content)
for element in file.elements:
    print("Find")
    #print(element.identifier)
    #print(element.content)
    for element2 in element.elements:
        print("Find2")
    #    print(element2.identifier)
    #    print(element2.content)