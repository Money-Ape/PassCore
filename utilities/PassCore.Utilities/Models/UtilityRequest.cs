namespace PassCore.Utilities.Models;

public sealed class UtilityRequest{
    public string Operation { get; set; } = string.Empty;
    public string? Path { get; set; }
    public bool Force { get; set; }
    public string? Destination { get; set; }
}