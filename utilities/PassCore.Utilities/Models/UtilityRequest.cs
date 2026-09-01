namespace PassCore.Utilities.Models;

public sealed class UtilityRequest{
    public string Operation { get; set; } = string.Empty;
    public string? Path { get; set; }
    public bool Force { get; set; }
    public string? Destination { get; set; }
    public string? ContainerDirectory { get; set; }
    public string? OutputPath { get; set; }
    public string? NoteTitle { get; set; }
    public string? AlbumName { get; set; }
    public string? ImageFilename { get; set; }
}