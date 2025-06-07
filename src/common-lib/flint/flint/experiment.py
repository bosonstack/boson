from aim import Run

def new_run(*args, **kwargs) -> Run:
    """Creates an Aim Run at default repository location."""
    
    return Run(repo="/aim-repo", *args, **kwargs)