import vtk

def main():
    list1 = [i for i in dir(vtk) if i.startswith('vtk')]
    list2 = []

    # objects that can be instantiated 
    for vtkobj in list1:
        try:
            a = getattr(vtk, vtkobj)()
        except:
            # if it can't be instantiated, we can't use it
            pass
        else:
            if a.IsA('vtkProcessObject'):
                if a.IsA('vtkSource'):
                    # all sources get appended
                    list2.append(vtkobj)
                elif vtkobj.endswith('Writer'):
                    # classes that aren't sources but are writers
                    # can also be appended
                    list2.append(vtkobj)

    # list2 will now be parsed and modules will be generated
    # we have to start our conditionals with the most specific cases
    # and work down to the more general cases.
    if vtkobj.endswith('Writer'):
        pass
    elif vtkobj.endswith('Reader'):
        pass

if __name__ == '__main__':
    main()
